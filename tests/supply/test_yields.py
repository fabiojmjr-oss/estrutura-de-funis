from __future__ import annotations

import pandas as pd
import pytest

from funilab.supply import hidden_factory, perfect_order, yield_table


@pytest.fixture
def attempts() -> pd.DataFrame:
    """Four orders through two stages. X: one repeat, Y: one repeat and one fallout."""
    rows = [
        ("o1", "X", 1, True, True),
        ("o2", "X", 2, False, True),
        ("o3", "X", 1, True, True),
        ("o4", "X", 1, True, True),
        ("o1", "Y", 1, True, True),
        ("o2", "Y", 1, True, True),
        ("o3", "Y", 3, False, False),
        ("o4", "Y", 2, False, True),
    ]
    return pd.DataFrame(rows, columns=["order_id", "stage", "attempts", "first_pass", "passed"])


def test_yield_table_by_hand(attempts: pd.DataFrame) -> None:
    table = yield_table(attempts, ["X", "Y"])
    assert table.loc["X", "first_pass_yield"] == pytest.approx(0.75)
    assert table.loc["Y", "first_pass_yield"] == pytest.approx(0.5)
    assert table.loc["Y", "final_yield"] == pytest.approx(0.75)
    assert table.loc["total", "first_pass_yield"] == pytest.approx(0.375)  # RTY
    assert table.loc["total", "final_yield"] == pytest.approx(0.75)
    assert table.loc["Y", "rework_per_100"] == pytest.approx(75.0)


def test_hidden_factory(attempts: pd.DataFrame) -> None:
    orders = pd.DataFrame({"order_id": ["o1", "o2", "o3", "o4"]})
    factory = hidden_factory(attempts, orders)
    assert factory["repeat_attempts"] == 4
    assert factory["repeat_share"] == pytest.approx(4 / 12)
    assert factory["orders_reworked_share"] == pytest.approx(3 / 4)


def test_perfect_order_product_versus_joint() -> None:
    # The same two orders fail both components: joint 50%, product 25%.
    orders = pd.DataFrame(
        {
            "status": ["delivered"] * 4 + ["cancelled"],
            "a": [True, True, False, False, False],
            "b": [True, True, False, False, False],
        }
    )
    table = perfect_order(orders, ("a", "b"))["rate"]
    assert table["product (assumes independence)"] == pytest.approx(0.25)
    assert table["joint (measured)"] == pytest.approx(0.5)
