"""Synthetic strategy execution funnel: initiatives from proposal to measured benefit.

Initiatives start arriving a year before the horizon, so the portfolio at ``as_of`` carries the
work in progress a real one does. The rate at which they are *approved* is higher than the rate
at which they are *delivered*, which is the ordinary condition of a portfolio and the reason its
lead time grows while every individual project reports green.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..management.stages import EXECUTION
from .config import SynthConfig, arrival_times

# Probability of passing each gate after the proposal.
PASS_RATE: tuple[float, ...] = (0.60, 0.80, 0.92, 0.72, 0.55)
# Median days to reach each stage from the one before.
MEDIAN_DAYS: tuple[float, ...] = (25.0, 35.0, 30.0, 150.0, 90.0)
AREAS = ("Operações", "Comercial", "Tecnologia", "Pessoas")


@dataclass(frozen=True)
class ManagementData:
    initiatives: pd.DataFrame
    events: pd.DataFrame


def generate_management(config: SynthConfig | None = None) -> ManagementData:
    """Initiatives with planned and realised benefit, and the stages each reached."""
    config = config or SynthConfig()
    rng = config.rng(4)

    proposed = arrival_times(rng, config, 0.8, offset_days=365)
    n = len(proposed)
    planned = rng.lognormal(np.log(400_000), 0.8, n).round(-3)
    # Execution slows as more initiatives are running at once: the load factor rises with the
    # arrival rate, standing in for the queueing a shared delivery team produces.
    load = 1 + 0.6 * np.linspace(0, 1, n)

    # Annotated as plain ndarrays: older NumPy stubs track shape and reject the reassignments.
    now: np.ndarray = proposed.to_numpy().copy()
    alive: np.ndarray = np.ones(n, dtype=bool)
    stage_ts: dict[str, np.ndarray] = {EXECUTION.top: now.copy()}
    stopped_ts = np.full(n, np.datetime64("NaT"), dtype="datetime64[ns]")
    stopped_at = np.full(n, "", dtype=object)
    for stage, rate, median in zip(EXECUTION.stages[1:], PASS_RATE, MEDIAN_DAYS, strict=True):
        passes = alive & (rng.random(n) < rate)
        scale = median * (load if stage == "Entregue" else 1.0)
        days = rng.lognormal(np.log(scale), 0.45, n)
        # A failed gate is decided part-way through the time the stage would have taken: a
        # rejection comes before an approval would have, and a project is stopped in flight.
        stop = alive & ~passes
        partial = pd.to_timedelta(days * rng.uniform(0.3, 1.0, n), unit="D").to_numpy()
        stopped_ts[stop] = now[stop] + partial[stop]
        stopped_at[stop] = stage
        alive = passes
        now = now + pd.to_timedelta(days, unit="D").to_numpy()
        stage_ts[stage] = np.where(alive, now, np.datetime64("NaT"))

    as_of64 = np.datetime64(config.as_of)
    observed = {
        stage: np.where(ts <= as_of64, ts, np.datetime64("NaT")) for stage, ts in stage_ts.items()
    }
    measured = ~np.isnat(observed[EXECUTION.bottom])
    # Realised benefit as a share of plan: centred well below one, which is the usual finding
    # of any benefits-realisation review, with a tail that over-delivers.
    realised_share = rng.beta(2.2, 2.0, n) * 1.3

    initiatives = pd.DataFrame(
        {
            "initiative_id": [f"IN{i:04d}" for i in range(n)],
            "area": rng.choice(AREAS, n),
            "planned_benefit": planned,
            "realised_benefit": np.where(measured, (planned * realised_share).round(-3), np.nan),
            "proposed_ts": proposed,
            "started_ts": observed["Em execução"],
            "delivered_ts": observed["Entregue"],
            "stopped_ts": np.where(stopped_ts <= as_of64, stopped_ts, np.datetime64("NaT")),
        }
    )
    stopped = ~np.isnat(initiatives["stopped_ts"].to_numpy())
    initiatives["stopped_at"] = np.where(stopped, stopped_at, "")
    initiatives["status"] = np.select(
        [measured, stopped], ["measured", "stopped"], default="in_flight"
    )
    events = (
        pd.DataFrame(observed)
        .assign(entity_id=initiatives["initiative_id"])
        .melt(id_vars="entity_id", var_name="stage", value_name="ts")
        .dropna(subset=["ts"])
        .sort_values(["entity_id", "ts"], ignore_index=True)
    )
    return ManagementData(initiatives=initiatives, events=events)
