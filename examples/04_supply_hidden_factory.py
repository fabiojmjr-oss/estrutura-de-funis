"""The fulfilment funnel's final yield, and the factory hidden behind it.

Run:
    python examples/04_supply_hidden_factory.py
"""

from __future__ import annotations

import pandas as pd

from funilab.supply import FULFILMENT, hidden_factory, perfect_order, yield_table
from funilab.synth import generate_supply


def main() -> None:
    pd.set_option("display.width", 160)
    data = generate_supply()

    print("1. First-pass yield against final yield, stage by stage")
    table = yield_table(data.attempts, FULFILMENT.stages[1:])
    print(table.round(4).to_string())
    rty = table.loc["total", "first_pass_yield"]
    final = table.loc["total", "final_yield"]
    print(
        f"\n   Final yield {final:.1%}: almost nothing is lost. Rolled throughput yield {rty:.1%}:"
        f"\n   one order in {1 / (1 - rty):.1f} is touched twice somewhere. The funnel report"
        "\n   shows the first number; the cost sits in the second."
    )

    factory = hidden_factory(data.attempts, data.orders)
    print(
        f"\n2. The hidden factory: {factory['repeat_attempts']:,.0f} repeat attempts,"
        f" {factory['repeat_share']:.1%} of all work, on"
        f" {factory['orders_reworked_share']:.1%} of orders."
    )

    print("\n3. Perfect order: product of components against the joint rate")
    print(perfect_order(data.orders).round(4).to_string())
    print(
        "\n   Here the two agree to a hundredth of a point, because the shared driver (order"
        "\n   complexity) moves each component only slightly. The check costs one line and the"
        "\n   function returns both, rather than assuming either way."
    )


if __name__ == "__main__":
    main()
