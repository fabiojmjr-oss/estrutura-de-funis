"""Synthetic idea portfolio: what each idea truly is, and what the team believes about it.

Every idea carries two sets of columns. The **latent** ones - whether the problem is real,
whether the proposed solution fits it, the value if it scales, the true rates an experiment
would measure - are what the world knows and nobody in the room does. The **estimated** ones -
RICE and ICE inputs - are what the team writes on the card at capture.

Keeping both is the point. A gate policy can only be judged by what it does to ideas whose truth
is known, and a scoring model can only be judged against the value it was trying to predict.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import SynthConfig, arrival_times


@dataclass(frozen=True)
class SourceProfile:
    """Where ideas come from, and how often the problem behind them is real."""

    name: str
    share: float
    real_problem_rate: float


DEFAULT_SOURCES: tuple[SourceProfile, ...] = (
    SourceProfile("Colaborador", 0.45, 0.30),
    SourceProfile("Cliente", 0.25, 0.50),
    SourceProfile("Dados", 0.15, 0.45),
    SourceProfile("Parceiro", 0.15, 0.35),
)

# Probability the first proposed solution fits a real problem.
SOLUTION_FIT_RATE = 0.45

# True rates an experiment would converge to. Real problems are confirmed by more interviewees;
# fitting solutions convert more smoke-test visitors; good MVPs retain more users.
PAIN_RATE = {"real": 0.55, "not_real": 0.18}
SIGNUP_RATE = {"good": 0.07, "real_no_fit": 0.03, "not_real": 0.015}
RETENTION_RATE = {"good": 0.45, "not_good": 0.22}


@dataclass(frozen=True)
class IdeationData:
    ideas: pd.DataFrame


def _beta_around(
    rng: np.random.Generator, mean: np.ndarray, concentration: float = 40.0
) -> np.ndarray:
    return rng.beta(mean * concentration, (1 - mean) * concentration)


def generate_ideas(
    config: SynthConfig | None = None,
    sources: tuple[SourceProfile, ...] = DEFAULT_SOURCES,
    *,
    ideas_per_day: float = 1.4,
) -> IdeationData:
    """An idea portfolio captured over the horizon, with its latent truth and its scorecards."""
    config = config or SynthConfig()
    rng = config.rng(5)

    captured = arrival_times(rng, config, ideas_per_day)
    n = len(captured)
    shares = np.array([s.share for s in sources])
    source_index = rng.choice(len(sources), n, p=shares / shares.sum())
    real = rng.random(n) < np.array([s.real_problem_rate for s in sources])[source_index]
    fit = real & (rng.random(n) < SOLUTION_FIT_RATE)
    value = rng.lognormal(np.log(300_000), 1.0, n).round(-3)

    pain = _beta_around(rng, np.where(real, PAIN_RATE["real"], PAIN_RATE["not_real"]))
    signup_mean = np.where(
        fit,
        SIGNUP_RATE["good"],
        np.where(real, SIGNUP_RATE["real_no_fit"], SIGNUP_RATE["not_real"]),
    )
    signup = _beta_around(rng, signup_mean, concentration=300.0)
    retention = _beta_around(rng, np.where(fit, RETENTION_RATE["good"], RETENTION_RATE["not_good"]))

    # The scorecard. Impact is a noisy read of value, reach is a noisy read of whether the
    # problem is common, confidence is almost pure opinion, and effort is roughly right. Those
    # are the ordinary properties of estimates made before any evidence exists.
    log_value = np.log(value / 300_000)
    impact_signal = log_value + 0.8 * real + rng.normal(0, 1.2, n)
    impact = np.select(
        [impact_signal < -1.0, impact_signal < 0.0, impact_signal < 0.8, impact_signal < 1.6],
        [0.25, 0.5, 1.0, 2.0],
        default=3.0,
    )
    reach = np.clip(np.round(5 + 1.5 * real + rng.normal(0, 2.2, n)), 1, 10)
    confidence = rng.choice([0.5, 0.8, 1.0], n, p=[0.25, 0.45, 0.30])
    effort = np.clip(np.round(rng.lognormal(np.log(3), 0.6, n), 1), 0.5, 12)
    ease = np.clip(np.round(11 - effort), 1, 10)

    ideas = pd.DataFrame(
        {
            "idea_id": [f"ID{i:04d}" for i in range(n)],
            "captured_ts": captured,
            "source": np.array([s.name for s in sources])[source_index],
            # Estimated at capture
            "reach": reach,
            "impact": impact,
            "confidence": confidence,
            "effort": effort,
            "ease": ease,
            # Latent truth
            "problem_real": real,
            "solution_fit": fit,
            "value_if_scaled": value,
            "true_pain_rate": pain,
            "true_signup_rate": signup,
            "true_retention": retention,
        }
    )
    return IdeationData(ideas=ideas)
