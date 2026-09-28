"""What a customer costs, and which channel deserves the credit.

Run:
    python examples/02_marketing_acquisition.py

Two conventions decide the answer before any analysis starts: which customers go in the CAC
denominator, and which touch in a journey gets the customer.
"""

from __future__ import annotations

import pandas as pd

from funilab.marketing import attribution_table, cac_by_attribution, cac_table
from funilab.synth import SynthConfig, generate_marketing


def main() -> None:
    pd.set_option("display.width", 160)
    config = SynthConfig()
    data = generate_marketing(config)
    start, end = config.start_ts, config.as_of

    print("1. CAC: the denominator is a decision")
    table = cac_table(data.leads, data.spend, start=start, end=end)
    print(table.round(0).to_string())
    paid = table.loc["paid (total)", "cac"]
    blended = table.loc["blended (total)", "cac"]
    print(
        f"\n   Blended CAC {blended:,.0f} vs paid CAC {paid:,.0f}: blended reads"
        f" {1 - blended / paid:.0%} cheaper because it divides media spend by customers media"
        "\n   did not buy. It is the number that cannot be bought more of."
    )

    customers = data.leads.loc[data.leads["Cliente"].between(start, end), "lead_id"]
    print("\n2. Attribution: who gets the customer")
    print(attribution_table(data.touches, customers).round(1).to_string())

    print("\n3. CAC per channel under each model")
    spend = data.spend.loc[data.spend["month"].between(start, end)].groupby("channel")["spend"]
    print(cac_by_attribution(data.touches, customers, spend.sum()).round(0).to_string())
    print(
        "\n   Events is the cheapest paid channel under first touch and the most expensive under"
        "\n   last touch. The budget decision flips on a convention nobody put on the slide."
    )


if __name__ == "__main__":
    main()
