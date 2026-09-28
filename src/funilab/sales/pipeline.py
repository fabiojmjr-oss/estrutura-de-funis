"""Win rate, stage probabilities and the weighted forecast.

A weighted pipeline multiplies each open deal by the probability of its stage. Almost every CRM
ships those probabilities as round numbers, and almost no one replaces them with the pipeline's
own history, so the forecast is a product of real amounts and invented odds. This module
estimates the odds from closed deals and prices the difference.
"""

from __future__ import annotations

from collections.abc import Mapping

import pandas as pd

from ..core import Funnel, reached


def win_rates(opportunities: pd.DataFrame) -> pd.DataFrame:
    """Win rate under four conventions, from the same opportunities.

    =====================  ==================================================================
    Convention             Definition
    =====================  ==================================================================
    count_closed           won / (won + lost), by number of deals - the usual report
    count_all              won / every opportunity, open ones counted as not won
    value_closed           won amount / closed amount
    value_all              won amount / all amount
    =====================  ==================================================================
    """
    won = opportunities["status"] == "won"
    closed = opportunities["status"].isin(["won", "lost"])
    amount = opportunities["amount"]
    rows = {
        "count_closed": won.sum() / closed.sum(),
        "count_all": won.sum() / len(opportunities),
        "value_closed": amount[won].sum() / amount[closed].sum(),
        "value_all": amount[won].sum() / amount.sum(),
    }
    return pd.Series(rows, name="win_rate").to_frame()


def stage_probabilities(
    events: pd.DataFrame, opportunities: pd.DataFrame, funnel: Funnel
) -> pd.Series:
    """Historical probability that a deal which reached each open stage was eventually won.

    Only closed deals are used, because an open deal's outcome is not yet known and counting it
    as a loss would bias every probability down.
    """
    wide = reached(events, funnel)
    status = opportunities.set_index("opp_id")["status"].reindex(wide.index)
    closed = status.isin(["won", "lost"])
    won = status == "won"
    probabilities = {}
    for stage in funnel.stages[:-1]:
        at_stage = wide[stage].notna() & closed
        probabilities[stage] = float((at_stage & won).sum() / at_stage.sum())
    return pd.Series(probabilities, name="historical")


def weighted_forecast(
    opportunities: pd.DataFrame, probabilities: Mapping[str, float] | pd.Series
) -> float:
    """Expected won amount from open deals: amount times the probability of the current stage."""
    open_deals = opportunities.loc[opportunities["status"] == "open"]
    weights = open_deals["current_stage"].map(pd.Series(probabilities, dtype=float))
    if weights.isna().any():
        missing = sorted(open_deals.loc[weights.isna(), "current_stage"].unique())
        raise ValueError(f"no probability given for stages {missing}")
    return float((open_deals["amount"] * weights).sum())


def stage_age(opportunities: pd.DataFrame, as_of: pd.Timestamp) -> pd.Series:
    """Days each open deal has spent in its current stage at ``as_of``."""
    open_deals = opportunities.loc[opportunities["status"] == "open"]
    return ((as_of - open_deals["stage_entered_ts"]).dt.total_seconds() / 86_400).rename(
        "days_in_stage"
    )


def stale_threshold(events: pd.DataFrame, opportunities: pd.DataFrame, funnel: Funnel) -> pd.Series:
    """Per open stage, the 85th percentile of days that eventually-won deals spent there.

    A deal older than this in its stage is slower than 85% of the deals that were won from it,
    which is the observable signal that it is probably not going to be.
    """
    wide = reached(events, funnel)
    won_ids = opportunities.loc[opportunities["status"] == "won", "opp_id"]
    won = wide.loc[wide.index.intersection(pd.Index(won_ids))]
    limits = {}
    for current, following in funnel.transitions:
        days = (won[following] - won[current]).dt.total_seconds() / 86_400
        limits[current] = float(days[days > 0].quantile(0.85))
    return pd.Series(limits, name="stale_after_days")


def sales_velocity(opportunities: pd.DataFrame) -> float:
    """Revenue per day: deals x win rate x average won deal / average days to close.

    Computed on closed deals only. It is an identity rather than a model, which is its use: the
    four factors are the only levers, and the formula shows how each trades against the others.
    """
    closed = opportunities.loc[opportunities["status"].isin(["won", "lost"])]
    won = closed.loc[closed["status"] == "won"]
    cycle = (won["close_ts"] - won["created_ts"]).dt.total_seconds().mean() / 86_400
    return float(len(closed) * (len(won) / len(closed)) * won["amount"].mean() / cycle)


def forecast_table(
    events: pd.DataFrame,
    opportunities: pd.DataFrame,
    funnel: Funnel,
    as_of: pd.Timestamp,
    crm_probabilities: Mapping[str, float],
) -> pd.DataFrame:
    """The open pipeline's expected won amount under three sets of odds.

    ========================  ================================================================
    Forecast                  Odds
    ========================  ================================================================
    crm_default               the probabilities the CRM was configured with
    historical                each stage's win rate among closed deals that reached it
    historical_fresh          the same, with stale deals (see :func:`stale_threshold`) at zero
    ========================  ================================================================

    If ``opportunities`` carries ``eventual_status`` - which only synthetic data can - the table
    adds the amount actually won from today's open deals and each forecast's error against it.
    """
    history = stage_probabilities(events, opportunities, funnel)
    limits = stale_threshold(events, opportunities, funnel)
    open_deals = opportunities.loc[opportunities["status"] == "open"].copy()
    age = stage_age(opportunities, as_of)
    stale = age > open_deals["current_stage"].map(limits)
    fresh_odds = open_deals["current_stage"].map(history).where(~stale, 0.0)

    rows = {
        "crm_default": weighted_forecast(opportunities, crm_probabilities),
        "historical": weighted_forecast(opportunities, history),
        "historical_fresh": float((open_deals["amount"] * fresh_odds).sum()),
    }
    table = pd.Series(rows, name="forecast").to_frame()
    if "eventual_status" in open_deals:
        actual = float(open_deals.loc[open_deals["eventual_status"] == "won", "amount"].sum())
        table["actual"] = actual
        table["error"] = table["forecast"] / actual - 1
    table.attrs["stale_deals"] = int(stale.sum())
    table.attrs["stale_amount"] = float(open_deals.loc[stale, "amount"].sum())
    return table
