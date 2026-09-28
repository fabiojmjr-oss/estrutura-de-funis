from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from funilab.core import (
    Funnel,
    FunnelDataError,
    conversion_sensitivity,
    funnel_table,
    period_rates,
    reached,
    wilson_interval,
)


def test_funnel_rejects_duplicates_and_single_stage() -> None:
    with pytest.raises(ValueError):
        Funnel("x", ("A",))
    with pytest.raises(ValueError):
        Funnel("x", ("A", "B", "A"))


def test_funnel_transitions(funnel: Funnel) -> None:
    assert funnel.transitions == [("A", "B"), ("B", "C")]
    assert funnel.top == "A" and funnel.bottom == "C"


def test_validation_reports_every_problem_at_once(events: pd.DataFrame, funnel: Funnel) -> None:
    bad = events.copy()
    bad.loc[0, "stage"] = "Z"
    bad["ts"] = bad["ts"].astype(str)
    with pytest.raises(FunnelDataError) as error:
        reached(bad, funnel)
    assert "not in funnel" in str(error.value)
    assert "not a datetime" in str(error.value)


def test_missing_columns_raise(events: pd.DataFrame, funnel: Funnel) -> None:
    with pytest.raises(FunnelDataError, match="missing columns"):
        reached(events.drop(columns="ts"), funnel)


def test_reached_infers_skipped_stages(events: pd.DataFrame, funnel: Funnel) -> None:
    wide = reached(events, funnel)
    assert wide.loc["e4", "A"] == pd.Timestamp("2025-01-04")  # back-filled from B
    assert wide.loc["e4", "entry_ts"] == pd.Timestamp("2025-01-04")
    literal = reached(events, funnel, skipped="literal")
    assert pd.isna(literal.loc["e4", "A"])


def test_reached_rejects_unknown_convention(events: pd.DataFrame, funnel: Funnel) -> None:
    with pytest.raises(ValueError):
        reached(events, funnel, skipped="guess")  # type: ignore[arg-type]


def test_funnel_table_by_hand(events: pd.DataFrame, funnel: Funnel) -> None:
    table = funnel_table(events, funnel)
    assert table["entered"].tolist() == [5, 4, 2]
    assert table.loc["B", "step_rate"] == pytest.approx(4 / 5)
    assert table.loc["C", "step_rate"] == pytest.approx(2 / 4)
    assert table.loc["C", "cumulative_rate"] == pytest.approx(2 / 5)


def test_literal_lets_a_step_rate_exceed_one(events: pd.DataFrame, funnel: Funnel) -> None:
    table = funnel_table(events, funnel, skipped="literal")
    # A is reached by e1, e2, e3, e5 only; B by e1, e2, e4, e5.
    assert table["entered"].tolist() == [4, 4, 2]
    three = events[events["entity_id"] != "e5"]
    literal = funnel_table(three, funnel, skipped="literal")
    assert literal.loc["B", "step_rate"] == pytest.approx(3 / 3)


def test_window_excludes_slow_conversions(events: pd.DataFrame, funnel: Funnel) -> None:
    table = funnel_table(events, funnel, window=pd.Timedelta(days=10))
    assert table.loc["C", "entered"] == 1  # e4 took 26 days


def test_mature_only_drops_recent_entries(events: pd.DataFrame, funnel: Funnel) -> None:
    table = funnel_table(
        events,
        funnel,
        window=pd.Timedelta(days=30),
        as_of=pd.Timestamp("2025-03-01"),
        mature_only=True,
    )
    assert table.loc["A", "entered"] == 4  # e5 entered Feb 20, window not closed


def test_mature_only_requires_window_and_as_of(events: pd.DataFrame, funnel: Funnel) -> None:
    with pytest.raises(ValueError):
        funnel_table(events, funnel, mature_only=True)


def test_entered_between_and_by_segment(events: pd.DataFrame, funnel: Funnel) -> None:
    table = funnel_table(
        events,
        funnel,
        entered_between=(pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-31")),
    )
    assert table.loc["A", "entered"] == 4
    segment = pd.Series({"e1": "x", "e2": "x", "e3": "y", "e4": "y", "e5": "y"}, name="seg")
    split = funnel_table(events, funnel, by=segment)
    assert split.loc[("x", "C"), "entered"] == 1
    assert split.loc[("y", "A"), "entered"] == 3


def test_period_rates_count_each_stage_by_its_own_date(
    events: pd.DataFrame, funnel: Funnel
) -> None:
    table = period_rates(
        events, funnel, start=pd.Timestamp("2025-01-01"), end=pd.Timestamp("2025-01-31")
    )
    assert table["entered"].tolist() == [4, 3, 2]


def test_conversion_sensitivity_rows(events: pd.DataFrame, funnel: Funnel) -> None:
    table = conversion_sensitivity(
        events,
        funnel,
        start=pd.Timestamp("2025-01-01"),
        end=pd.Timestamp("2025-03-01"),
        window=pd.Timedelta(days=20),
        as_of=pd.Timestamp("2025-03-01"),
    )
    assert list(table.index) == [
        "period",
        "cohort_all",
        "cohort_window",
        "cohort_matured",
        "cohort_literal",
    ]
    assert table.loc["cohort_all", "end_to_end"] == pytest.approx(2 / 5)
    assert table.loc["cohort_window", "end_to_end"] == pytest.approx(1 / 5)
    assert table.loc["cohort_matured", "end_to_end"] == pytest.approx(1 / 4)
    assert table.loc["cohort_literal", "end_to_end"] == pytest.approx(1 / 3)


def test_wilson_matches_published_values() -> None:
    low, high = wilson_interval(5, 10)
    assert float(low) == pytest.approx(0.2366, abs=1e-4)
    assert float(high) == pytest.approx(0.7634, abs=1e-4)
    low, high = wilson_interval(0, 10)
    assert float(low) == pytest.approx(0.0, abs=1e-12)
    assert float(high) == pytest.approx(0.2775, abs=1e-4)


def test_wilson_is_vectorised() -> None:
    low, high = wilson_interval(np.array([1, 50]), np.array([10, 100]))
    assert low.shape == (2,) and (low < high).all()
