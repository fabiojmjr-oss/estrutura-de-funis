"""Which stage to work on, and how much top of funnel a target needs.

A funnel's output is the top multiplied by every step rate, so the arithmetic of improvement has
two facts that are routinely confused:

* A **relative** lift of 10% at any stage lifts the output by exactly 10%. No stage is special.
* An **absolute** lift of one point lifts the output by ``1 / rate`` percent, so the lowest rate
  in the chain is where a point is worth most.

"Fix the worst stage" is therefore true in points and false in percent, and neither statement
says which lift is cheaper to buy. The lever that deserves the money is decided by the cost of
the lift, which no funnel report contains.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


def expected_output(top: float, rates: Mapping[str, float] | pd.Series) -> float:
    """Entities expected at the bottom, given the top and every step rate."""
    return float(top * np.prod(list(pd.Series(rates, dtype=float))))


def required_top(target: float, rates: Mapping[str, float] | pd.Series) -> float:
    """The reverse funnel: how many entities must enter to deliver ``target`` at the bottom."""
    product = float(np.prod(list(pd.Series(rates, dtype=float))))
    if product <= 0:
        raise ValueError("a zero rate makes every target unreachable")
    return target / product


def lever_table(
    rates: Mapping[str, float] | pd.Series,
    top: float,
    *,
    absolute: float = 0.01,
    relative: float = 0.10,
) -> pd.DataFrame:
    """The gain in output from lifting each step rate, in points and in percent.

    Args:
        rates: Step rate per transition, in funnel order.
        top: Entities entering the funnel.
        absolute: Lift in rate points (0.01 is one point).
        relative: Lift as a share of the current rate (0.10 is ten percent).

    Returns:
        One row per transition with the current ``rate``, the output gain from the absolute lift
        and from the relative lift, and ``rank_absolute``: 1 is the stage where a point is worth
        most.
    """
    series = pd.Series(rates, dtype=float)
    if ((series <= 0) | (series > 1)).any():
        raise ValueError("step rates must be in (0, 1]")
    base = expected_output(top, series)
    rows = []
    for stage, rate in series.items():
        lifted_abs = min(rate + absolute, 1.0)
        rows.append(
            {
                "transition": stage,
                "rate": rate,
                "gain_absolute": base * (lifted_abs / rate - 1),
                "gain_relative": base * (min(rate * (1 + relative), 1.0) / rate - 1),
            }
        )
    table = pd.DataFrame(rows).set_index("transition")
    table["gain_absolute_pct"] = table["gain_absolute"] / base
    table["rank_absolute"] = table["gain_absolute"].rank(ascending=False, method="min").astype(int)
    return table
