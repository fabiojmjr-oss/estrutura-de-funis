"""Configuration for the synthetic data generator."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SynthConfig:
    """Parameters shared by every synthetic funnel.

    The horizon ends mid-flight on purpose. Leads created in December have not had time to
    become customers, deals opened last month are still open, and initiatives approved this
    quarter have not delivered. That censoring is the most common reason a funnel report is
    wrong, and a generator without it would make every convention look equivalent.

    ``growth`` is monthly and applies to every volume. A growing business is what separates a
    period rate from a cohort rate, so it is on by default.

    ``history_days`` starts the slower funnels (marketing, sales) that long before the horizon, so
    they are warm on day one. Without it, January's customers could only come from January's
    leads, and every period rate in the first months would be an artefact of the generator.
    """

    seed: int = 42
    start: str = "2025-01-01"
    days: int = 365
    growth: float = 0.04
    history_days: int = 180

    @property
    def start_ts(self) -> pd.Timestamp:
        return pd.Timestamp(self.start)

    @property
    def as_of(self) -> pd.Timestamp:
        """The observation date: the end of the horizon."""
        return self.start_ts + pd.Timedelta(days=self.days)

    def rng(self, stream: int) -> np.random.Generator:
        """An independent generator per funnel, so adding one never moves another's numbers."""
        return np.random.default_rng([self.seed, stream])


def arrival_times(
    rng: np.random.Generator, config: SynthConfig, per_day: float, *, offset_days: int = 0
) -> pd.DatetimeIndex:
    """Arrival timestamps from a Poisson process whose rate grows by ``config.growth`` a month.

    ``offset_days`` shifts the start back, for funnels whose entities began before the horizon.
    """
    total_days = config.days + offset_days
    day = np.arange(total_days)
    rate = per_day * (1 + config.growth) ** ((day - offset_days) / 30.4)
    counts = rng.poisson(rate)
    base = np.repeat(day, counts).astype(float) + rng.random(int(counts.sum()))
    origin = config.start_ts - pd.Timedelta(days=offset_days)
    return pd.DatetimeIndex(origin + pd.to_timedelta(np.sort(base), unit="D"))
