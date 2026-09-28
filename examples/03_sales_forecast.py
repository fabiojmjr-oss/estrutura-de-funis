"""What the open pipeline will actually close, and why the CRM overstates it.

Run:
    python examples/03_sales_forecast.py

The synthetic pipeline carries each open deal's eventual outcome, which is what lets this script
grade the forecast. A real one would have to wait a quarter to be graded.
"""

from __future__ import annotations

import pandas as pd

from funilab.core import funnel_table
from funilab.sales import (
    CRM_DEFAULT_PROBABILITY,
    PIPELINE,
    forecast_table,
    stage_probabilities,
    win_rates,
)
from funilab.synth import SynthConfig, generate_sales


def main() -> None:
    pd.set_option("display.width", 160)
    config = SynthConfig()
    data = generate_sales(config)

    print("1. A deal created at proposal: did it pass qualification?")
    for skipped in ("infer", "literal"):
        table = funnel_table(data.events, PIPELINE, skipped=skipped)
        print(f"\n   skipped={skipped!r}")
        print(table.round(4).to_string())
    print(
        "\n   Counting only what was logged puts more deals at proposal than at qualification: a"
        "\n   step rate above 100%. Any stage-to-stage target set on it is set on an artefact."
    )

    print("\n2. Four win rates from one pipeline")
    print(win_rates(data.opportunities).round(4).to_string())

    print("\n3. Stage odds: configured against measured")
    history = stage_probabilities(data.events, data.opportunities, PIPELINE)
    print(pd.DataFrame({"crm": CRM_DEFAULT_PROBABILITY, "historical": history}).round(3))

    print("\n4. The forecast, graded")
    table = forecast_table(
        data.events, data.opportunities, PIPELINE, config.as_of, CRM_DEFAULT_PROBABILITY
    )
    print(table.round(3).to_string())
    print(
        f"\n   {table.attrs['stale_deals']} stale deals carry"
        f" {table.attrs['stale_amount'] / 1e6:.1f}M of open amount. Better odds do not fix the"
        "\n   forecast; removing deals whose age already says 'no' does."
    )


if __name__ == "__main__":
    main()
