from __future__ import annotations

import pandas as pd
import pytest

from funilab.core import Funnel
from funilab.sales import (
    forecast_table,
    sales_velocity,
    stage_age,
    stage_probabilities,
    stale_threshold,
    weighted_forecast,
    win_rates,
)

F = Funnel("s", ("P", "Q", "W"))


@pytest.fixture
def opportunities() -> pd.DataFrame:
    """Two won (10 and 90), one lost (100), one open at Q (50)."""
    return pd.DataFrame(
        {
            "opp_id": ["o1", "o2", "o3", "o4"],
            "amount": [10.0, 90.0, 100.0, 50.0],
            "status": ["won", "won", "lost", "open"],
            "current_stage": ["W", "W", "Q", "Q"],
            "created_ts": pd.to_datetime(["2025-01-01"] * 4),
            "stage_entered_ts": pd.to_datetime(
                ["2025-01-11", "2025-01-21", "2025-01-05", "2025-01-02"]
            ),
            "close_ts": pd.to_datetime(["2025-01-11", "2025-01-21", "2025-01-15", None]),
            "eventual_status": ["won", "won", "lost", "lost"],
        }
    )


@pytest.fixture
def events() -> pd.DataFrame:
    rows = [
        ("o1", "P", "2025-01-01"),
        ("o1", "Q", "2025-01-03"),
        ("o1", "W", "2025-01-11"),
        ("o2", "P", "2025-01-01"),
        ("o2", "Q", "2025-01-05"),
        ("o2", "W", "2025-01-21"),
        ("o3", "P", "2025-01-01"),
        ("o3", "Q", "2025-01-05"),
        ("o4", "P", "2025-01-01"),
        ("o4", "Q", "2025-01-02"),
    ]
    frame = pd.DataFrame(rows, columns=["entity_id", "stage", "ts"])
    frame["ts"] = pd.to_datetime(frame["ts"])
    return frame


def test_four_win_rates_by_hand(opportunities: pd.DataFrame) -> None:
    table = win_rates(opportunities)["win_rate"]
    assert table["count_closed"] == pytest.approx(2 / 3)
    assert table["count_all"] == pytest.approx(2 / 4)
    assert table["value_closed"] == pytest.approx(100 / 200)
    assert table["value_all"] == pytest.approx(100 / 250)


def test_stage_probabilities_ignore_open_deals(
    events: pd.DataFrame, opportunities: pd.DataFrame
) -> None:
    probabilities = stage_probabilities(events, opportunities, F)
    assert probabilities["P"] == pytest.approx(2 / 3)
    assert probabilities["Q"] == pytest.approx(2 / 3)


def test_weighted_forecast(opportunities: pd.DataFrame) -> None:
    assert weighted_forecast(opportunities, {"P": 0.1, "Q": 0.4}) == pytest.approx(20.0)
    with pytest.raises(ValueError, match="no probability"):
        weighted_forecast(opportunities, {"P": 0.1})


def test_stale_threshold_and_age(events: pd.DataFrame, opportunities: pd.DataFrame) -> None:
    limits = stale_threshold(events, opportunities, F)
    # Won deals spent 8 and 16 days at Q: the 85th percentile interpolates to 14.8.
    assert limits["Q"] == pytest.approx(14.8)
    age = stage_age(opportunities, pd.Timestamp("2025-01-22"))
    assert age.loc[3] == pytest.approx(20.0)


def test_forecast_table_grades_against_the_eventual_outcome(
    events: pd.DataFrame, opportunities: pd.DataFrame
) -> None:
    table = forecast_table(
        events, opportunities, F, pd.Timestamp("2025-01-22"), {"P": 0.1, "Q": 0.4}
    )
    assert table.loc["crm_default", "forecast"] == pytest.approx(20.0)
    assert table.loc["historical", "forecast"] == pytest.approx(50 * 2 / 3)
    assert table.loc["historical_fresh", "forecast"] == pytest.approx(0.0)  # 20 days > 14.8
    assert table.attrs["stale_deals"] == 1
    assert table["actual"].iloc[0] == 0.0


def test_sales_velocity(opportunities: pd.DataFrame) -> None:
    # 3 closed x 2/3 won x mean won 50 / mean cycle 15 days = 6.67 a day.
    assert sales_velocity(opportunities) == pytest.approx(3 * (2 / 3) * 50 / 15)
