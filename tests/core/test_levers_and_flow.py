from __future__ import annotations

import pandas as pd
import pytest

from funilab.core import (
    Funnel,
    expected_output,
    lever_table,
    littles_law,
    required_top,
    stage_durations,
)

RATES = {"B": 0.5, "C": 0.2, "D": 0.8}


def test_expected_output_and_reverse_funnel() -> None:
    assert expected_output(1000, RATES) == pytest.approx(80.0)
    assert required_top(80, RATES) == pytest.approx(1000.0)


def test_required_top_rejects_zero_rate() -> None:
    with pytest.raises(ValueError):
        required_top(10, {"B": 0.0})


def test_relative_lift_is_equal_everywhere_and_points_favour_the_lowest_rate() -> None:
    table = lever_table(RATES, 1000)
    assert table["gain_relative"].tolist() == pytest.approx([8.0, 8.0, 8.0])
    assert table.loc["C", "rank_absolute"] == 1
    # One point on a 20% rate is +5% of output; on 80% it is +1.25%.
    assert table.loc["C", "gain_absolute_pct"] == pytest.approx(0.05)
    assert table.loc["D", "gain_absolute_pct"] == pytest.approx(0.0125)


def test_lever_table_validates_rates() -> None:
    with pytest.raises(ValueError):
        lever_table({"B": 1.2}, 100)


def test_stage_durations_by_hand(events: pd.DataFrame, funnel: Funnel) -> None:
    table = stage_durations(events, funnel)
    ab = table.loc["A -> B"]
    # e1 2 days, e2 4 days, e4 0 days (A inferred from B), e5 1 day.
    assert ab["n"] == 4
    assert ab["zero_day"] == 1
    assert ab["median_days"] == pytest.approx(1.5)
    bc = table.loc["B -> C"]
    assert bc["n"] == 2 and bc["mean_days"] == pytest.approx((7 + 26) / 2)


def test_littles_law_on_a_steady_system() -> None:
    # One item enters every day and stays exactly 10 days: WIP 10, throughput 1, lead time 10.
    start = pd.date_range("2025-01-01", periods=200, freq="D")
    items = pd.DataFrame({"start": start, "end": start + pd.Timedelta(days=10)})
    result = littles_law(
        items,
        start="start",
        end="end",
        window_start=pd.Timestamp("2025-03-01"),
        window_end=pd.Timestamp("2025-06-01"),
    )
    assert result.wip == pytest.approx(10.0)
    assert result.throughput_per_day == pytest.approx(1.0)
    assert result.lead_time_days == pytest.approx(10.0)
    assert result.implied_lead_time == pytest.approx(10.0)
    assert result.lead_time_at_wip(5) == pytest.approx(5.0)


def test_littles_law_counts_open_items_to_the_window_end() -> None:
    items = pd.DataFrame({"start": [pd.Timestamp("2025-01-01")], "end": [pd.NaT]})
    result = littles_law(
        items,
        start="start",
        end="end",
        window_start=pd.Timestamp("2025-01-01"),
        window_end=pd.Timestamp("2025-01-11"),
    )
    assert result.wip == pytest.approx(1.0)
    assert result.completed == 0


def test_littles_law_rejects_empty_window() -> None:
    items = pd.DataFrame({"start": [pd.Timestamp("2025-01-01")], "end": [pd.NaT]})
    with pytest.raises(ValueError):
        littles_law(
            items,
            start="start",
            end="end",
            window_start=pd.Timestamp("2025-01-02"),
            window_end=pd.Timestamp("2025-01-01"),
        )
