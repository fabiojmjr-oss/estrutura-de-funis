"""Time in the funnel: stage durations and Little's law.

A conversion rate says how many; it says nothing about how long. Two funnels with identical rates
can deliver the same output a quarter apart, and in a pipeline with a target date that quarter is
the whole difference.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .conversion import Skipped, reached
from .funnel import Funnel


def stage_durations(
    events: pd.DataFrame, funnel: Funnel, *, skipped: Skipped = "infer"
) -> pd.DataFrame:
    """Days from each stage to the next, for the entities that made the transition.

    Under ``skipped="infer"`` a skipped stage is back-filled with the next stage's time, so its
    transition takes zero days. That is the honest reading - no time was spent there - but it
    pulls the median towards zero, so the count of zero-day transitions is returned beside it.
    """
    wide = reached(events, funnel, skipped=skipped)
    rows = []
    for current, following in funnel.transitions:
        both = wide[[current, following]].dropna()
        days = (both[following] - both[current]).dt.total_seconds() / 86_400
        rows.append(
            {
                "transition": f"{current} -> {following}",
                "n": len(days),
                "zero_day": int((days == 0).sum()),
                "median_days": float(days.median()) if len(days) else float("nan"),
                "p85_days": float(days.quantile(0.85)) if len(days) else float("nan"),
                "mean_days": float(days.mean()) if len(days) else float("nan"),
            }
        )
    return pd.DataFrame(rows).set_index("transition")


@dataclass(frozen=True)
class LittleResult:
    """Little's law measured on a window: ``WIP = throughput x lead time``.

    ``lead_time_days`` is measured on the items completed in the window; ``implied_lead_time`` is
    ``wip / throughput``. They agree when the system is stable, and the gap between them is a
    measure of how far it is from stable - a growing backlog makes the measured lead time of what
    finished understate what is still waiting.
    """

    wip: float
    throughput_per_day: float
    lead_time_days: float
    implied_lead_time: float
    completed: int

    def lead_time_at_wip(self, wip_cap: float) -> float:
        """Lead time if WIP were capped at ``wip_cap`` at the same throughput."""
        return wip_cap / self.throughput_per_day


def littles_law(
    items: pd.DataFrame,
    *,
    start: str,
    end: str,
    window_start: pd.Timestamp,
    window_end: pd.Timestamp,
) -> LittleResult:
    """Time-averaged WIP, throughput and lead time of the items in ``items`` over a window.

    Args:
        items: One row per work item.
        start: Column holding when the item entered the system.
        end: Column holding when it left (``NaT`` if it has not).
    """
    span_days = (window_end - window_start).total_seconds() / 86_400
    if span_days <= 0:
        raise ValueError("the window must have positive length")
    entered = items[start]
    left = items[end].fillna(window_end)
    overlap_start = entered.where(entered > window_start, window_start)
    overlap_end = left.where(left < window_end, window_end)
    overlap = (overlap_end - overlap_start).dt.total_seconds().clip(lower=0) / 86_400
    wip = float(overlap.sum() / span_days)

    # Half-open (start, end], so consecutive windows never count a completion twice.
    done = items[(items[end] > window_start) & (items[end] <= window_end)]
    throughput = len(done) / span_days
    lead = (done[end] - done[start]).dt.total_seconds() / 86_400
    return LittleResult(
        wip=wip,
        throughput_per_day=throughput,
        lead_time_days=float(lead.mean()) if len(done) else float("nan"),
        implied_lead_time=wip / throughput if throughput else float("nan"),
        completed=len(done),
    )
