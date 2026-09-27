"""Synthetic order fulfilment funnel, with the rework the final yield does not show.

Every stage after the order can fail on the first attempt. A failed attempt is usually caught and
repeated - a credit analysis re-run, a line re-picked after checking, a redelivery - so most
failures never reach the customer and never reach the final yield either. They are logged in
``attempts``, which is where the hidden factory lives.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..supply.stages import FULFILMENT
from .config import SynthConfig, arrival_times

# First-pass yield of each transition for a five-line order at an average site.
FIRST_PASS: tuple[float, ...] = (0.93, 0.95, 0.965, 0.975, 0.92)
# Hours of work (or elapsed time) per attempt at each transition.
STAGE_HOURS: tuple[float, ...] = (3.0, 4.0, 1.0, 5.0, 20.0)
# Probability a repeated attempt passes, and how many attempts are made before giving up.
RETRY_PASS = 0.85
MAX_ATTEMPTS = 3
PROMISE_HOURS = 60.0
SITES: dict[str, float] = {"CD-Norte": -0.25, "CD-Centro": 0.20, "CD-Sul": 0.0}


@dataclass(frozen=True)
class SupplyData:
    orders: pd.DataFrame
    attempts: pd.DataFrame
    events: pd.DataFrame


def generate_supply(
    config: SynthConfig | None = None, *, orders_per_day: float = 55.0
) -> SupplyData:
    """Orders through credit, picking, checking, dispatch and delivery, with every attempt."""
    config = config or SynthConfig()
    rng = config.rng(3)

    order_ts = arrival_times(rng, config, orders_per_day)
    n = len(order_ts)
    site_names = np.array(list(SITES))
    site_index = rng.integers(0, len(SITES), n)
    site_effect = np.array(list(SITES.values()))[site_index]
    lines = 1 + rng.poisson(4.0, n)
    # A complex order fails more often at *every* stage, which is what makes stage yields
    # correlated and the product of component rates a biased estimate of the joint rate.
    difficulty = -0.10 * (lines - 5) + site_effect

    now = order_ts.to_numpy().copy()
    alive = np.ones(n, dtype=bool)
    stage_ts = {FULFILMENT.top: now.copy()}
    attempt_rows = []
    total_rework = np.zeros(n, dtype=int)

    for stage, base, hours in zip(FULFILMENT.stages[1:], FIRST_PASS, STAGE_HOURS, strict=True):
        logit = np.log(base / (1 - base)) + difficulty
        first = alive & (rng.random(n) < 1 / (1 + np.exp(-logit)))
        attempts = np.where(alive, 1, 0)
        passed = first.copy()
        for _ in range(MAX_ATTEMPTS - 1):
            retry = alive & ~passed
            attempts[retry] += 1
            passed |= retry & (rng.random(n) < RETRY_PASS)
        elapsed = rng.gamma(2.0, hours / 2.0, n) * np.maximum(attempts, 1)
        now = now + pd.to_timedelta(elapsed, unit="h").to_numpy()
        attempt_rows.append(
            pd.DataFrame(
                {
                    "order_index": np.flatnonzero(alive),
                    "stage": stage,
                    "attempts": attempts[alive],
                    "first_pass": first[alive],
                    "passed": passed[alive],
                }
            )
        )
        total_rework += np.where(alive, attempts - 1, 0)
        alive &= passed
        stage_ts[stage] = np.where(alive, now, np.datetime64("NaT"))

    as_of64 = np.datetime64(config.as_of)
    delivered_ts = stage_ts[FULFILMENT.bottom]
    delivered = ~np.isnat(delivered_ts) & (delivered_ts <= as_of64)
    lead_hours = (delivered_ts - order_ts.to_numpy()) / np.timedelta64(1, "h")

    def component(base: float, slope: float) -> np.ndarray:
        logit = np.log(base / (1 - base)) + slope * difficulty
        return rng.random(n) < 1 / (1 + np.exp(-logit))

    orders = pd.DataFrame(
        {
            "order_id": [f"P{i:06d}" for i in range(n)],
            "site": site_names[site_index],
            "lines": lines,
            "order_ts": order_ts,
            "status": np.where(
                delivered, "delivered", np.where(np.isnat(delivered_ts), "cancelled", "open")
            ),
            "rework_attempts": total_rework,
            "on_time": np.where(delivered, lead_hours <= PROMISE_HOURS, False),
            "in_full": np.where(delivered, component(0.975, 1.0), False),
            "damage_free": np.where(delivered, component(0.985, 0.8), False),
            "invoice_ok": np.where(delivered, component(0.98, 0.8), False),
        }
    )
    # A cancelled order whose last attempt would land after as_of is still being worked.
    fallout = orders["status"] == "cancelled"
    last_seen = pd.Series(now, index=orders.index)
    orders.loc[fallout & (last_seen > config.as_of), "status"] = "open"

    attempt_log = pd.concat(attempt_rows, ignore_index=True)
    order_index = attempt_log.pop("order_index").to_numpy()
    attempt_log.insert(0, "order_id", orders["order_id"].to_numpy()[order_index])

    events = (
        pd.DataFrame(stage_ts)
        .assign(entity_id=orders["order_id"])
        .melt(id_vars="entity_id", var_name="stage", value_name="ts")
        .dropna(subset=["ts"])
    )
    events = events.loc[events["ts"] <= config.as_of].sort_values(
        ["entity_id", "ts"], ignore_index=True
    )
    return SupplyData(orders=orders, attempts=attempt_log, events=events)
