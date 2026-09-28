"""The full cycle: from captured idea to scaled solution, under five gate policies.

Run:
    python examples/07_idea_to_mvp.py

Every policy runs on a portfolio whose truth is known, so the script can count what no real
pipeline can: the good ideas a policy killed, and the bad ones it scaled. The calibrated policy
was chosen by grid search on the seed-42 portfolio, so it is reported on an independent one.
"""

from __future__ import annotations

import pandas as pd

from funilab.core import funnel_table
from funilab.ideation import (
    BASELINE_POLICIES,
    IDEA_TO_SOLUTION,
    CycleCosts,
    compare_policies,
    simulate_policy,
    stage_value,
)
from funilab.synth import SynthConfig, generate_ideas

HOLDOUT = SynthConfig(seed=2026)


def main() -> None:
    pd.set_option("display.width", 180)
    ideas = generate_ideas(HOLDOUT).ideas
    print(f"Portfolio: {len(ideas)} ideas, {int(ideas['solution_fit'].sum())} genuinely good.\n")

    print("1. Five policies, 30 replications each (mean, and the 2.5-97.5% range of runs)")
    table = compare_policies(ideas, replications=30)
    means = table["mean"].unstack("metric")
    view = means[
        ["mvps_built", "good_scaled", "bad_scaled", "false_kills", "spend", "net_value"]
    ].copy()
    view[["spend", "net_value"]] /= 1e6
    print(view.round(1).to_string())
    print("\n   net value range (BRL M):")
    net = table.xs("net_value", level="metric")[["low", "high"]] / 1e6
    print(net.round(1).to_string())

    print("\n2. The funnel the calibrated policy produces")
    run = simulate_policy(ideas, BASELINE_POLICIES[-1], seed=1)
    print(funnel_table(run.events, IDEA_TO_SOLUTION).round(3).to_string())

    print("\n3. What an idea is worth at each stage (calibrated pass rates, default costs)")
    counts = funnel_table(run.events, IDEA_TO_SOLUTION)["entered"]
    rates = (counts.shift(-1) / counts).iloc[:-1]
    costs = CycleCosts()
    per_stage = [
        costs.triage,
        5 * costs.per_interview,
        costs.smoke_fixed + 600 * 2.0,
        costs.mvp_build,
        costs.mvp_fixed + 60 * costs.per_user,
        0.0,
    ]
    payoff = float(ideas.loc[ideas["solution_fit"], "value_if_scaled"].mean())
    values = stage_value(list(rates.index), list(rates), per_stage, payoff)
    print(values.round({"expected_value": 0, "cost_to_go": 0, "p_success": 3}).to_string())
    print(
        "\n   The idea did not change between capture and validation; the evidence removed the"
        "\n   ways it could fail. That rise in expected value is what each gate's spend buys."
    )


if __name__ == "__main__":
    main()
