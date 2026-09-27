"""Synthetic marketing funnel: leads, the touches before them, spend and first-year margin."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..marketing.stages import MARKETING
from .config import SynthConfig, arrival_times


@dataclass(frozen=True)
class ChannelProfile:
    """One acquisition channel.

    Attributes:
        name: Channel label.
        paid: Whether the channel carries media spend.
        leads_per_day: Lead volume at the start of the horizon.
        monthly_spend: Media spend per month at the start of the horizon, in BRL.
        step_rates: Probability of Lead->MQL, MQL->SQL and SQL->Cliente.
    """

    name: str
    paid: bool
    leads_per_day: float
    monthly_spend: float
    step_rates: tuple[float, float, float]


DEFAULT_CHANNELS: tuple[ChannelProfile, ...] = (
    ChannelProfile("Busca paga", True, 16.0, 55_000.0, (0.45, 0.35, 0.22)),
    ChannelProfile("Social pago", True, 30.0, 48_000.0, (0.25, 0.22, 0.14)),
    ChannelProfile("Eventos", True, 5.0, 32_000.0, (0.60, 0.42, 0.26)),
    ChannelProfile("Indicação", False, 4.0, 0.0, (0.70, 0.55, 0.35)),
    ChannelProfile("Orgânico", False, 14.0, 0.0, (0.35, 0.25, 0.16)),
)

# Mean days between consecutive stages. SQL to customer is a sales cycle, so it is the longest.
STAGE_DELAY_DAYS: tuple[float, float, float] = (6.0, 14.0, 35.0)

# Brand search closes journeys other channels opened: when a journey has more than one touch,
# this is the chance the last one is a paid search click.
LAST_TOUCH_SEARCH_SHARE = 0.5


@dataclass(frozen=True)
class MarketingData:
    leads: pd.DataFrame
    events: pd.DataFrame
    touches: pd.DataFrame
    spend: pd.DataFrame


def generate_marketing(
    config: SynthConfig | None = None,
    channels: tuple[ChannelProfile, ...] = DEFAULT_CHANNELS,
) -> MarketingData:
    """Leads by source channel, the stages they reached by ``as_of``, touches and spend."""
    config = config or SynthConfig()
    rng = config.rng(1)
    as_of = config.as_of

    frames = []
    for profile in channels:
        created = arrival_times(rng, config, profile.leads_per_day, offset_days=config.history_days)
        frame = pd.DataFrame({"created_ts": created, "channel": profile.name})
        ts = frame["created_ts"].to_numpy()
        alive = np.ones(len(frame), dtype=bool)
        for step, (rate, delay) in enumerate(
            zip(profile.step_rates, STAGE_DELAY_DAYS, strict=True), start=1
        ):
            alive &= rng.random(len(frame)) < rate
            ts = ts + pd.to_timedelta(rng.gamma(2.0, delay / 2.0, len(frame)), unit="D").to_numpy()
            frame[MARKETING.stages[step]] = np.where(alive, ts, np.datetime64("NaT"))
        frames.append(frame)

    leads = pd.concat(frames, ignore_index=True).sort_values("created_ts", ignore_index=True)
    leads.insert(0, "lead_id", [f"L{i:06d}" for i in range(len(leads))])
    leads["first_year_margin"] = np.where(
        leads["Cliente"].notna(), rng.lognormal(np.log(18_000), 0.6, len(leads)), 0.0
    )

    events = [leads[["lead_id", "created_ts"]].set_axis(["entity_id", "ts"], axis=1)]
    events[0]["stage"] = MARKETING.top
    for stage in MARKETING.stages[1:]:
        part = leads.loc[leads[stage].notna(), ["lead_id", stage]].set_axis(
            ["entity_id", "ts"], axis=1
        )
        part["stage"] = stage
        events.append(part)
    log = pd.concat(events, ignore_index=True)
    log = log.loc[log["ts"] <= as_of, ["entity_id", "stage", "ts"]].reset_index(drop=True)

    for stage in MARKETING.stages[1:]:
        leads.loc[leads[stage] > as_of, stage] = pd.NaT
    leads.loc[leads["Cliente"].isna(), "first_year_margin"] = 0.0

    return MarketingData(
        leads=leads,
        events=log,
        touches=_touches(rng, leads, channels),
        spend=_spend(config, channels),
    )


def _touches(
    rng: np.random.Generator, leads: pd.DataFrame, channels: tuple[ChannelProfile, ...]
) -> pd.DataFrame:
    """The marketing touches in each lead's journey, the first one being the source channel.

    Middle touches are drawn in proportion to each channel's lead volume.
    """
    names = [profile.name for profile in channels]
    weights = np.array([profile.leads_per_day for profile in channels])
    n_touches = np.minimum(1 + rng.poisson(1.4, len(leads)), 5)
    lead_ids = np.repeat(leads["lead_id"].to_numpy(), n_touches)
    order = np.concatenate([np.arange(n) for n in n_touches])
    channel = rng.choice(names, size=len(lead_ids), p=weights / weights.sum())
    first = order == 0
    channel[first] = leads["channel"].to_numpy()
    last = np.r_[order[1:] == 0, True] & ~first
    search = rng.random(len(lead_ids)) < LAST_TOUCH_SEARCH_SHARE
    channel[last & search] = "Busca paga"
    return pd.DataFrame({"lead_id": lead_ids, "touch": order, "channel": channel})


def _spend(config: SynthConfig, channels: tuple[ChannelProfile, ...]) -> pd.DataFrame:
    first = config.start_ts - pd.Timedelta(days=config.history_days)
    months = pd.date_range(first.to_period("M").to_timestamp(), config.as_of, freq="MS")
    months = months[months < config.as_of]
    rows = [
        {
            "month": month,
            "channel": profile.name,
            "spend": profile.monthly_spend
            * (1 + config.growth) ** ((month - config.start_ts).days / 30.4),
        }
        for month in months
        for profile in channels
        if profile.paid
    ]
    return pd.DataFrame(rows)
