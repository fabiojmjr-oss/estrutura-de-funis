"""From announced benefit to realised benefit, and why the portfolio keeps slowing down.

Run:
    python examples/05_strategy_execution.py
"""

from __future__ import annotations

import pandas as pd

from funilab.management import EXECUTION, benefit_bridge, execution_flow
from funilab.synth import SynthConfig, generate_management


def main() -> None:
    pd.set_option("display.width", 160)
    config = SynthConfig()
    data = generate_management(config)
    initiatives = data.initiatives

    print("1. The benefit bridge, on the cohort proposed a full year before the horizon")
    cohort = initiatives.loc[initiatives["proposed_ts"] < config.start_ts]
    bridge = benefit_bridge(cohort, EXECUTION)
    shown = bridge.assign(benefit_m=bridge["benefit"] / 1e6).drop(columns="benefit")
    print(shown.round(3).to_string())
    unmeasured = -bridge.loc["stopped before Benefício medido", "benefit"]
    realised = bridge.loc["realised", "benefit"]
    print(
        f"\n   {unmeasured / 1e6:.1f}M of planned benefit was delivered and never measured, against"
        f"\n   {realised / 1e6:.1f}M realised and measured. The portfolio cannot say whether its"
        "\n   largest single outcome happened."
    )

    print("\n2. Little's law on execution, first and second half of the year")
    half = config.start_ts + pd.Timedelta(days=182)
    for label, start, end in (
        ("H1", config.start_ts, half),
        ("H2", half, config.as_of),
    ):
        flow = execution_flow(initiatives, window_start=start, window_end=end)
        monthly = flow.throughput_per_day * 30
        print(
            f"   {label}: WIP {flow.wip:5.1f}, throughput {monthly:4.1f}/month, lead time"
            f" measured {flow.lead_time_days:4.0f} d, implied {flow.implied_lead_time:4.0f} d"
        )
    year = execution_flow(initiatives, window_start=config.start_ts, window_end=config.as_of)
    print(
        f"\n   Over the year: WIP {year.wip:.1f}, implied lead time {year.implied_lead_time:.0f} d."
        f"\n   Measured on what finished, it is {year.lead_time_days:.0f} d - the backlog is still"
        "\n   inside the system. Halving WIP at the same throughput implies"
        f" {year.lead_time_at_wip(year.wip / 2):.0f} d."
    )


if __name__ == "__main__":
    main()
