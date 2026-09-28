"""Conversion rates under explicit conventions.

The arithmetic of a funnel is a chain of ratios. What decides whether the ratio is right is three
choices that are rarely written down:

* **skipped stages** - an entity recorded at a later stage with no record at an earlier one (a
  deal created directly at proposal, an order that bypassed credit) either passed through the
  earlier stage or did not. ``"infer"`` assumes it did; ``"literal"`` counts only what was logged,
  which lets a step rate exceed 100%.
* **basis** - a *cohort* rate follows the same entities from entry; a *period* rate divides this
  month's stage entries by this month's entries at the stage before, which are different people.
* **maturity** - a cohort that entered last week has not had time to convert. Counting it in the
  denominator reads delay as failure.

Every function here takes those choices as arguments, and :func:`conversion_sensitivity` returns
the same funnel under each of them side by side, because the gap is usually the finding.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from .funnel import Funnel, validate_events

Skipped = Literal["infer", "literal"]


def reached(events: pd.DataFrame, funnel: Funnel, *, skipped: Skipped = "infer") -> pd.DataFrame:
    """One row per entity, one column per stage, holding the time the stage was first reached.

    Args:
        events: Event log with ``entity_id``, ``stage`` and ``ts``.
        funnel: The stage order.
        skipped: ``"infer"`` back-fills an unrecorded stage with the time of the next recorded one,
            on the reasoning that reaching proposal implies having been qualified. ``"literal"``
            leaves it empty.

    Returns:
        Frame indexed by ``entity_id`` with a datetime column per stage (``NaT`` if not reached)
        and an ``entry_ts`` column: the earliest recorded timestamp of the entity.
    """
    validate_events(events, funnel)
    wide = (
        events.groupby(["entity_id", "stage"], observed=True)["ts"]
        .min()
        .unstack("stage")
        .reindex(columns=list(funnel.stages))
    )
    entry = wide.min(axis=1)
    if skipped == "infer":
        wide = wide.bfill(axis=1)
    elif skipped != "literal":
        raise ValueError(f"skipped must be 'infer' or 'literal', got {skipped!r}")
    wide.columns.name = None
    wide["entry_ts"] = entry
    return wide


def _counts(wide: pd.DataFrame, funnel: Funnel, window: pd.Timedelta | None) -> pd.Series:
    counts = {}
    for stage in funnel.stages:
        hit = wide[stage].notna()
        if window is not None:
            hit &= (wide[stage] - wide["entry_ts"]) <= window
        counts[stage] = int(hit.sum())
    return pd.Series(counts, name="entered")


def _table_from_counts(counts: pd.Series) -> pd.DataFrame:
    table = counts.to_frame()
    previous = counts.shift(1)
    table["step_rate"] = counts / previous
    top = counts.iloc[0]
    table["cumulative_rate"] = counts / top if top else np.nan
    table.index.name = "stage"
    return table


def funnel_table(
    events: pd.DataFrame,
    funnel: Funnel,
    *,
    skipped: Skipped = "infer",
    window: pd.Timedelta | None = None,
    entered_between: tuple[pd.Timestamp, pd.Timestamp] | None = None,
    as_of: pd.Timestamp | None = None,
    mature_only: bool = False,
    by: pd.Series | None = None,
) -> pd.DataFrame:
    """Cohort funnel: how many entities reached each stage, and the rates between stages.

    The cohort is every entity whose ``entry_ts`` falls in ``entered_between`` (all of them if
    omitted). The top-of-funnel count is the number of entities that reached the **first**
    stage, so under ``skipped="literal"`` entities that entered lower down are counted at their
    stage but not at the top, and step rates can exceed one. That is the defect the convention
    exists to expose, not an error to hide.

    Args:
        window: Count a stage only if reached within this long of entry.
        entered_between: Inclusive entry-date bounds of the cohort.
        as_of: Observation date. Required with ``mature_only``.
        mature_only: Keep only entities whose full ``window`` had elapsed by ``as_of``.
        by: Optional segment labels indexed by ``entity_id``. Adds an outer index level.

    Returns:
        One row per stage with ``entered``, ``step_rate`` and ``cumulative_rate``.
    """
    wide = reached(events, funnel, skipped=skipped)
    if entered_between is not None:
        start, end = entered_between
        wide = wide.loc[(wide["entry_ts"] >= start) & (wide["entry_ts"] <= end)]
    if mature_only:
        if window is None or as_of is None:
            raise ValueError("mature_only needs both window and as_of")
        wide = wide.loc[wide["entry_ts"] + window <= as_of]

    if by is None:
        return _table_from_counts(_counts(wide, funnel, window))

    labels = by.reindex(wide.index)
    parts = {
        segment: _table_from_counts(_counts(group, funnel, window))
        for segment, group in wide.groupby(labels, observed=True)
    }
    return pd.concat(parts, names=[by.name or "segment"])


def period_rates(
    events: pd.DataFrame,
    funnel: Funnel,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    skipped: Skipped = "infer",
) -> pd.DataFrame:
    """The dashboard convention: stage entries counted by the date each stage was reached.

    Every stage is counted by its own timestamp inside ``[start, end]``, so the numerator and the
    denominator of a step rate are different entities. In a growing business the denominator is
    systematically larger than the cohort that produced the numerator, and the rate reads low.
    """
    wide = reached(events, funnel, skipped=skipped)
    counts = pd.Series(
        {
            stage: int(((wide[stage] >= start) & (wide[stage] <= end)).sum())
            for stage in funnel.stages
        },
        name="entered",
    )
    return _table_from_counts(counts)


def conversion_sensitivity(
    events: pd.DataFrame,
    funnel: Funnel,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    window: pd.Timedelta,
    as_of: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """One event log, five conventions, the end-to-end rate under each.

    ==================  =========================================================================
    Convention          Definition
    ==================  =========================================================================
    period              stage entries by their own date in the period (the dashboard)
    cohort_all          entities entering in the period, whatever they reached by ``as_of``
    cohort_window       the same cohort, a stage counted only if reached within ``window``
    cohort_matured      as above, restricted to entities whose window had closed by ``as_of``
    cohort_literal      the matured cohort without inferring skipped stages
    ==================  =========================================================================

    Returns:
        One row per convention with ``top``, ``bottom``, ``end_to_end`` and ``entities``.
    """
    as_of = as_of if as_of is not None else end
    rows = []

    def row(name: str, table: pd.DataFrame, entities: int) -> None:
        top = int(table["entered"].iloc[0])
        bottom = int(table["entered"].iloc[-1])
        rows.append(
            {
                "convention": name,
                "top": top,
                "bottom": bottom,
                "end_to_end": bottom / top if top else np.nan,
                "entities": entities,
            }
        )

    wide = reached(events, funnel)
    in_period = int(((wide["entry_ts"] >= start) & (wide["entry_ts"] <= end)).sum())
    matured = int(
        (
            (wide["entry_ts"] >= start)
            & (wide["entry_ts"] <= end)
            & (wide["entry_ts"] + window <= as_of)
        ).sum()
    )

    period = period_rates(events, funnel, start=start, end=end)
    row("period", period, int(period["entered"].iloc[0]))
    bounds = (start, end)
    row("cohort_all", funnel_table(events, funnel, entered_between=bounds), in_period)
    row(
        "cohort_window",
        funnel_table(events, funnel, window=window, entered_between=bounds),
        in_period,
    )
    for name, skipped in (("cohort_matured", "infer"), ("cohort_literal", "literal")):
        table = funnel_table(
            events,
            funnel,
            skipped=skipped,  # type: ignore[arg-type]
            window=window,
            entered_between=bounds,
            as_of=as_of,
            mature_only=True,
        )
        row(name, table, matured)
    return pd.DataFrame(rows).set_index("convention")


def wilson_interval(
    successes: int | np.ndarray, trials: int | np.ndarray, confidence: float = 0.95
) -> tuple[np.ndarray, np.ndarray]:
    """Wilson score interval for a proportion.

    Preferred over the normal approximation because it stays inside [0, 1] and behaves at the
    small counts that the bottom of a funnel always has.
    """
    from statistics import NormalDist

    z = NormalDist().inv_cdf(0.5 + confidence / 2)
    k = np.asarray(successes, dtype=float)
    n = np.asarray(trials, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        p = k / n
        denominator = 1 + z**2 / n
        centre = (p + z**2 / (2 * n)) / denominator
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return centre - half, centre + half
