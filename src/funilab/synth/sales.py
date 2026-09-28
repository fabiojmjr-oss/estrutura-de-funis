"""Synthetic sales pipeline, observed at ``as_of`` with its eventual outcome kept aside.

The generator plays every opportunity to its end, then hides whatever happens after ``as_of``.
The hidden columns (``eventual_status``, ``eventual_close_ts``) are what a forecast made on the
observed pipeline is later judged against, which no real CRM extract can offer at the time.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..sales.stages import PIPELINE
from .config import SynthConfig, arrival_times

# Probability of advancing from each open stage to the next, for a median-sized deal.
ADVANCE_RATE: tuple[float, float, float, float] = (0.55, 0.60, 0.62, 0.58)
# Mean days spent in each open stage by a deal that advances.
STAGE_DAYS: tuple[float, float, float, float] = (9.0, 14.0, 18.0, 15.0)
# Share of opportunities created directly at the proposal stage (inbound requests for proposal).
DIRECT_TO_PROPOSAL = 0.20
MEDIAN_DEAL = 40_000.0
# Larger deals close less often and take longer; these set how strongly.
SIZE_LOGIT_SLOPE = 0.35
SIZE_TIME_EXPONENT = 0.30


@dataclass(frozen=True)
class SalesData:
    opportunities: pd.DataFrame
    events: pd.DataFrame


def _logit(p: np.ndarray | float) -> np.ndarray:
    return np.log(np.asarray(p) / (1 - np.asarray(p)))


def generate_sales(config: SynthConfig | None = None, *, reps: int = 8) -> SalesData:
    """Opportunities over the horizon, their stage history, and their eventual outcome."""
    config = config or SynthConfig()
    rng = config.rng(2)
    as_of = config.as_of

    created = arrival_times(rng, config, 6.0, offset_days=config.history_days)
    n = len(created)
    rep_names = np.array([f"V{r + 1:02d}" for r in range(reps)])
    rep_index = rng.integers(0, reps, n)
    rep_skill = rng.normal(0.0, 0.3, reps)[rep_index]
    amount = rng.lognormal(np.log(MEDIAN_DEAL), 0.9, n).round(-2)
    size = np.log(amount / MEDIAN_DEAL)
    entry = np.where(rng.random(n) < DIRECT_TO_PROPOSAL, 2, 0)

    stage_ts = np.full((n, len(PIPELINE.stages)), np.datetime64("NaT"), dtype="datetime64[ns]")
    rows = np.arange(n)
    stage_ts[rows, entry] = created.to_numpy()
    ended = np.zeros(n, dtype=bool)
    lost_ts = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    last_open = entry.copy()

    for step, (rate, days) in enumerate(zip(ADVANCE_RATE, STAGE_DAYS, strict=True)):
        here = (entry <= step) & ~ended
        if not here.any():
            continue
        prob = 1 / (1 + np.exp(-(_logit(rate) + rep_skill - SIZE_LOGIT_SLOPE * size)))
        advance = here & (rng.random(n) < prob)
        lose = here & ~advance
        scale = days * np.exp(SIZE_TIME_EXPONENT * size)
        win_days = rng.gamma(3.0, scale / 3.0)
        # Losses take longer and spread wider: a deal is rarely declared dead promptly.
        loss_days = rng.exponential(scale * 1.6)
        now = stage_ts[rows, step]
        stage_ts[advance, step + 1] = now[advance] + pd.to_timedelta(win_days[advance], unit="D")
        lost_ts[lose] = now[lose] + pd.to_timedelta(loss_days[lose], unit="D")
        last_open[advance] = step + 1
        ended |= lose

    won_ts = stage_ts[:, -1]
    eventual_status = np.where(~np.isnat(won_ts), "won", "lost")
    eventual_close = np.where(~np.isnat(won_ts), won_ts, lost_ts)

    as_of64 = np.datetime64(as_of)
    observed = np.where(stage_ts <= as_of64, stage_ts, np.datetime64("NaT"))
    status = np.where(
        eventual_close <= as_of64, eventual_status, "open"
    )  # anything not closed yet is open
    current_index = np.array([np.flatnonzero(~np.isnat(row)).max() for row in observed], dtype=int)

    opportunities = pd.DataFrame(
        {
            "opp_id": [f"OP{i:05d}" for i in range(n)],
            "rep": rep_names[rep_index],
            "amount": amount,
            "created_ts": created,
            "entry_stage": np.array(PIPELINE.stages)[entry],
            "current_stage": np.array(PIPELINE.stages)[current_index],
            "stage_entered_ts": observed[rows, current_index],
            "status": status,
            "close_ts": np.where(status != "open", eventual_close, np.datetime64("NaT")),
            "eventual_status": eventual_status,
            "eventual_close_ts": eventual_close,
        }
    )
    opportunities["close_ts"] = pd.to_datetime(opportunities["close_ts"])

    events = (
        pd.DataFrame(observed, columns=list(PIPELINE.stages))
        .assign(entity_id=opportunities["opp_id"])
        .melt(id_vars="entity_id", var_name="stage", value_name="ts")
        .dropna(subset=["ts"])
        .sort_values(["entity_id", "ts"], ignore_index=True)
    )
    return SalesData(opportunities=opportunities, events=events)
