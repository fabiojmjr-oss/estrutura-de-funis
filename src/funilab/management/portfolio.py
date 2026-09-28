"""Benefit leakage and the flow of a strategy portfolio.

A strategic plan announces the sum of every initiative's planned benefit. What reaches the income
statement is the benefit of the initiatives that were approved, funded, delivered *and measured*,
at the share of plan they actually realised. :func:`benefit_bridge` walks from one number to the
other and reconciles exactly, so every unit of leakage is attributed to the gate that lost it.

:func:`execution_flow` applies Little's law to the initiatives in execution. A portfolio whose
approvals outrun its deliveries grows its work in progress, and at constant throughput every
extra initiative in flight adds to the lead time of all the others - which is why starting less
is the cheapest way to finish sooner.
"""

from __future__ import annotations

import pandas as pd

from ..core import Funnel, LittleResult, littles_law


def benefit_bridge(initiatives: pd.DataFrame, funnel: Funnel) -> pd.DataFrame:
    """From announced benefit to realised benefit, one bar per source of leakage.

    Args:
        initiatives: ``planned_benefit``, ``realised_benefit``, ``status`` (``measured``,
            ``stopped`` or ``in_flight``) and ``stopped_at`` (the stage not reached).
        funnel: Stage order, used to order the gate bars.

    Returns:
        Bars in order: ``announced``, one ``stopped before <stage>`` per gate, ``still in
        flight``, ``under-delivered`` and ``realised``. The bars from ``announced`` downwards sum
        to ``realised`` exactly.
    """
    planned = initiatives["planned_benefit"]
    bars: dict[str, float] = {"announced": float(planned.sum())}
    stopped = initiatives["status"] == "stopped"
    for stage in funnel.stages[1:]:
        lost = float(planned[stopped & (initiatives["stopped_at"] == stage)].sum())
        bars[f"stopped before {stage}"] = -lost
    bars["still in flight"] = -float(planned[initiatives["status"] == "in_flight"].sum())
    measured = initiatives["status"] == "measured"
    realised = float(initiatives.loc[measured, "realised_benefit"].sum())
    bars["under-delivered"] = realised - float(planned[measured].sum())
    bars["realised"] = realised

    table = pd.Series(bars, name="benefit").to_frame()
    table["share_of_announced"] = table["benefit"] / bars["announced"]
    residual = table["benefit"].iloc[:-1].sum() - realised
    if abs(residual) > 1e-6 * max(bars["announced"], 1.0):
        raise AssertionError(f"benefit bridge does not reconcile: residual {residual}")
    return table


def execution_flow(
    initiatives: pd.DataFrame, *, window_start: pd.Timestamp, window_end: pd.Timestamp
) -> LittleResult:
    """Little's law on the execution stage: from start of work to delivery or stop."""
    running = initiatives.loc[initiatives["started_ts"].notna()].copy()
    stopped_in_flight = running["stopped_at"] == "Entregue"
    running["finished_ts"] = running["delivered_ts"].where(
        ~stopped_in_flight, running["stopped_ts"]
    )
    return littles_law(
        running,
        start="started_ts",
        end="finished_ts",
        window_start=window_start,
        window_end=window_end,
    )
