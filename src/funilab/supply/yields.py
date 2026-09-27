"""Stage yields, rolled throughput yield and the perfect order.

The final yield of a fulfilment funnel - orders delivered over orders placed - is usually close to
one, because almost every failure is caught and repeated before the customer sees it. That is
why it is the wrong number to manage by. **Rolled throughput yield** multiplies the *first-pass*
yield of every stage and answers a different question: what share of orders went through without
anyone touching them twice. The gap between the two is the hidden factory.

The perfect order has the mirror-image problem. It is often reported as the product of its
component rates, which assumes the components fail independently. They do not - the order that
is late is also the one more likely to be short - so the product and the joint rate differ, and
only the joint rate is what the customer experienced.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

PERFECT_ORDER_COMPONENTS: tuple[str, ...] = ("on_time", "in_full", "damage_free", "invoice_ok")


def yield_table(attempts: pd.DataFrame, stages: Sequence[str]) -> pd.DataFrame:
    """First-pass and final yield per stage, with the rework each stage generated.

    Args:
        attempts: One row per order and stage with ``attempts``, ``first_pass`` and ``passed``.
        stages: Stage order.

    Returns:
        One row per stage with ``units`` entering, ``first_pass_yield``, ``final_yield`` and
        ``rework_per_100`` (repeat attempts per hundred units), plus a ``total`` row holding
        rolled throughput yield and the product of final yields.
    """
    grouped = attempts.groupby("stage", sort=False)
    table = pd.DataFrame(
        {
            "units": grouped.size(),
            "first_pass_yield": grouped["first_pass"].mean(),
            "final_yield": grouped["passed"].mean(),
            "rework_per_100": grouped["attempts"].sum() / grouped.size() * 100 - 100,
        }
    ).reindex(list(stages))
    table.loc["total"] = [
        float(table["units"].iloc[0]),
        float(np.prod(table["first_pass_yield"])),
        float(np.prod(table["final_yield"])),
        float(table["rework_per_100"].sum()),
    ]
    table.index.name = "stage"
    return table


def perfect_order(
    orders: pd.DataFrame, components: Sequence[str] = PERFECT_ORDER_COMPONENTS
) -> pd.DataFrame:
    """Each component's rate on delivered orders, their product, and the joint rate.

    Returns:
        One row per component plus ``product (assumes independence)`` and ``joint (measured)``.
    """
    delivered = orders.loc[orders["status"] == "delivered", list(components)].astype(bool)
    rates = delivered.mean()
    rates.loc["product (assumes independence)"] = float(np.prod(rates[list(components)]))
    rates.loc["joint (measured)"] = float(delivered.all(axis=1).mean())
    return rates.rename("rate").to_frame()


def hidden_factory(attempts: pd.DataFrame, orders: pd.DataFrame) -> dict[str, float]:
    """How much work is repetition: repeat attempts, their share of all attempts, per order."""
    total = float(attempts["attempts"].sum())
    repeats = float((attempts["attempts"] - 1).sum())
    touched = attempts.loc[attempts["attempts"] > 1, "order_id"].nunique()
    return {
        "attempts": total,
        "repeat_attempts": repeats,
        "repeat_share": repeats / total,
        "orders_reworked_share": touched / len(orders),
    }
