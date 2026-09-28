"""The expected value of an idea at each stage, and what evidence is worth there.

Working backwards from the payoff, an idea entering stage ``i`` is worth the chance it clears
every remaining gate times the payoff, minus the cost of every test it will still have to pay
for. Two things follow that a funnel report does not show:

* The value of an idea **rises** as it passes gates, even though nothing about the idea changed,
  because the evidence removed the ways it could fail. Paying for a gate is buying that rise.
* A stage whose test costs more than the rise it buys should not be run - the idea should either
  go straight through or be stopped - and the break-even is computable before anyone runs it.
"""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def stage_value(
    stages: Sequence[str],
    pass_rates: Sequence[float],
    stage_costs: Sequence[float],
    payoff: float,
) -> pd.DataFrame:
    """Backward induction through a stage-gate cycle.

    Args:
        stages: Name of each stage, in order. The test run *in* stage ``i`` decides whether the
            idea reaches stage ``i + 1``.
        pass_rates: Probability of passing the test run in each stage.
        stage_costs: Cost of the test run in each stage.
        payoff: Value of an idea that clears every test.

    Returns:
        One row per stage with the ``expected_value`` of an idea entering it, the ``cost_to_go``
        (expected spend from here) and ``p_success`` (probability of clearing every remaining
        test). The final row is the payoff.
    """
    if not len(stages) == len(pass_rates) == len(stage_costs):
        raise ValueError("stages, pass_rates and stage_costs must have the same length")
    value = payoff
    p_success = 1.0
    cost_to_go = 0.0
    rows = [{"stage": "payoff", "expected_value": payoff, "cost_to_go": 0.0, "p_success": 1.0}]
    for stage, rate, cost in zip(
        reversed(stages), reversed(pass_rates), reversed(stage_costs), strict=True
    ):
        value = -cost + rate * value
        cost_to_go = cost + rate * cost_to_go
        p_success *= rate
        rows.append(
            {
                "stage": stage,
                "expected_value": value,
                "cost_to_go": cost_to_go,
                "p_success": p_success,
            }
        )
    return pd.DataFrame(rows[::-1]).set_index("stage")


def break_even_payoff(pass_rates: Sequence[float], stage_costs: Sequence[float]) -> float:
    """The payoff at which an idea entering the first stage has an expected value of zero."""
    probability = 1.0
    expected_cost = 0.0
    for rate, cost in zip(pass_rates, stage_costs, strict=True):
        expected_cost += probability * cost
        probability *= rate
    return expected_cost / probability
