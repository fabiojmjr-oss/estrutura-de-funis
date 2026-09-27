"""How much of a conversion rate is definition rather than performance.

Run:
    python examples/01_conversion_definition.py

One lead base, measured the five ways a funnel report can be built. The latest quarter looks
like a collapse under the cohort convention and looks stable under the period one, and neither
is the rate the quarter will end up converting at.
"""

from __future__ import annotations

import pandas as pd

from funilab.core import conversion_sensitivity, funnel_table, lever_table, required_top
from funilab.marketing import MARKETING
from funilab.synth import SynthConfig, generate_marketing

WINDOW = pd.Timedelta(days=120)


def main() -> None:
    pd.set_option("display.width", 160)
    config = SynthConfig()
    data = generate_marketing(config)

    print("1. The same funnel, five conventions, two quarters")
    for label, start, end in (
        ("Q3 (entered Jul-Sep)", "2025-07-01", "2025-09-30"),
        ("Q4 (entered Oct-Dec)", "2025-10-01", "2025-12-31"),
    ):
        table = conversion_sensitivity(
            data.events,
            MARKETING,
            start=pd.Timestamp(start),
            end=pd.Timestamp(end),
            window=WINDOW,
            as_of=config.as_of,
        )
        print(f"\n   {label}")
        print(table.round(4).to_string())
    print(
        "\n   Q4's cohort reads half of Q3's. Nothing about the leads changed: a lead that entered"
        "\n   in November has not had the 30-60 days a sales cycle takes. No Q4 cohort has matured,"
        "\n   so the only defensible statement about Q4's conversion today is 'not yet known'."
    )

    print("\n2. Where a point of conversion is worth most")
    matured = funnel_table(
        data.events, MARKETING, window=WINDOW, as_of=config.as_of, mature_only=True
    )
    rates = matured["step_rate"].dropna()
    print(lever_table(rates, top=10_000).round(4).to_string())
    print(
        "\n   A 10% relative lift is worth the same at every stage. A one-point lift is worth most"
        "\n   at the lowest rate. Which lift is cheaper to buy is not in the funnel."
    )

    print("\n3. The reverse funnel")
    target = 300
    print(f"   {target} customers a quarter need {required_top(target, rates):,.0f} leads.")


if __name__ == "__main__":
    main()
