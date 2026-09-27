"""Customer acquisition cost and attribution.

Two numbers every marketing review opens with, and both are conventions before they are
measurements:

* **CAC** divides spend by customers, and which customers go in the denominator decides the
  answer. Blended CAC counts customers from referral and organic, who cost no media; paid CAC
  does not. Blended always looks better and cannot be bought more of.
* **Attribution** decides which channel gets the customer. First touch rewards the channel that
  opened the journey, last touch the one that closed it, and the two can rank the same channels
  in opposite orders on the same data.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

Model = Literal["first", "last", "linear", "position"]
MODELS: tuple[Model, ...] = ("first", "last", "linear", "position")


def attribution(touches: pd.DataFrame, converted: pd.Index | list[str], model: Model) -> pd.Series:
    """Customers credited to each channel under one attribution model.

    Args:
        touches: ``lead_id``, ``touch`` (0-based order) and ``channel``.
        converted: The ``lead_id`` of every customer.
        model: ``first``, ``last``, ``linear`` (equal split) or ``position`` (40% first, 40% last,
            20% spread over the middle; a two-touch journey splits 50/50).

    Returns:
        Credited customers per channel. Sums exactly to the number of customers.
    """
    journeys = touches.loc[touches["lead_id"].isin(pd.Index(converted))].copy()
    journeys = journeys.sort_values(["lead_id", "touch"])
    size = journeys.groupby("lead_id")["touch"].transform("size")
    position = journeys.groupby("lead_id").cumcount()
    first = position == 0
    last = position == size - 1

    if model == "first":
        weight = first.astype(float)
    elif model == "last":
        weight = last.astype(float)
    elif model == "linear":
        weight = 1.0 / size
    elif model == "position":
        middle = (size - 2).clip(lower=1)
        weight = pd.Series(
            np.select(
                [size == 1, size == 2, first | last],
                [1.0, 0.5, 0.4],
                default=0.2 / middle,
            ),
            index=journeys.index,
        )
    else:
        raise ValueError(f"unknown attribution model {model!r}")

    return weight.groupby(journeys["channel"]).sum().rename(model)


def attribution_table(touches: pd.DataFrame, converted: pd.Index | list[str]) -> pd.DataFrame:
    """Every attribution model side by side, with each channel's rank under each."""
    table = pd.concat([attribution(touches, converted, model) for model in MODELS], axis=1)
    table = table.fillna(0.0)
    for model in MODELS:
        table[f"rank_{model}"] = table[model].rank(ascending=False, method="min").astype(int)
    return table.sort_values("last", ascending=False)


def cac_table(
    leads: pd.DataFrame,
    spend: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    customer_stage: str = "Cliente",
) -> pd.DataFrame:
    """Spend, customers and CAC per channel, plus the blended and paid totals.

    Customers are counted by the date they became customers, inside ``[start, end]``, which is
    the convention a monthly CAC report uses. Channel is the lead's source channel.

    Returns:
        One row per channel and two summary rows: ``paid (total)``, which divides paid spend by
        paid-channel customers, and ``blended (total)``, which divides the same spend by every
        customer.
    """
    in_period = leads[customer_stage].between(start, end)
    customers = leads.loc[in_period].groupby("channel").size().rename("customers")
    window = spend.loc[spend["month"].between(start, end)]
    cost = window.groupby("channel")["spend"].sum().rename("spend")
    table = pd.concat([cost, customers], axis=1).fillna(0.0)
    table["cac"] = table["spend"] / table["customers"].where(table["customers"] > 0)

    paid = table["spend"] > 0
    paid_spend = float(table.loc[paid, "spend"].sum())
    paid_customers = float(table.loc[paid, "customers"].sum())
    all_customers = float(table["customers"].sum())
    table.loc["paid (total)"] = [paid_spend, paid_customers, paid_spend / paid_customers]
    table.loc["blended (total)"] = [paid_spend, all_customers, paid_spend / all_customers]
    return table


def payback_months(cac: float, monthly_margin: float) -> float:
    """Months of contribution margin needed to recover one customer's acquisition cost."""
    if monthly_margin <= 0:
        return float("inf")
    return cac / monthly_margin


def cac_by_attribution(
    touches: pd.DataFrame, converted: pd.Index | list[str], spend: pd.Series
) -> pd.DataFrame:
    """CAC per paid channel under every attribution model.

    Args:
        touches: Journeys, as for :func:`attribution`.
        converted: The customers whose acquisition the spend paid for.
        spend: Media spend per channel over the same period.

    Returns:
        One row per channel with spend, and the CAC and rank (1 = cheapest) under each model.
        Channels without spend are left out: they have no acquisition cost to attribute.
    """
    credits = attribution_table(touches, converted)[list(MODELS)]
    paid = spend[spend > 0]
    table = pd.DataFrame({"spend": paid})
    for model in MODELS:
        table[f"cac_{model}"] = paid / credits[model].reindex(paid.index)
    for model in MODELS:
        table[f"rank_{model}"] = table[f"cac_{model}"].rank(method="min").astype(int)
    return table
