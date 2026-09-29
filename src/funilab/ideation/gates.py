"""Gate policies for the idea-to-solution cycle, and what each one costs and returns.

A gate policy is four choices: how many captured ideas triage lets through, how much evidence is
collected at each validation gate, where the bar sits, and how the evidence is read against the
bar. :func:`simulate_policy` runs one policy over a portfolio whose truth is known, so it can
count what no real pipeline can: the good ideas it killed and the bad ideas it scaled.

Every result is stochastic - an interview panel is a sample - so :func:`compare_policies`
replicates each policy and reports an interval, and a difference whose interval covers zero is
reported as one rather than as a small win.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from .evidence import prob_above
from .scoring import ice, rice
from .stages import IDEA_TO_SOLUTION

Reading = Literal["point", "posterior"]


@dataclass(frozen=True)
class GatePolicy:
    """How ideas are let through the cycle.

    Attributes:
        name: Label used in reports.
        triage_share: Share of captured ideas passed to validation, taken from the top of the
            score. ``1.0`` passes everything.
        triage_score: ``rice``, ``ice`` or ``none`` (a random draw of ``triage_share``).
        interviews: Problem interviews per idea.
        pain_bar: Bar on the true share of interviewees who confirm the pain.
        visitors: Smoke-test visitors per idea.
        signup_bar: Bar on the true smoke-test sign-up rate.
        mvp_users: Users given the MVP.
        retention_bar: Bar on the true share who keep using it.
        reading: ``point`` advances when the observed rate reaches the bar - how most teams read
            a small sample. ``posterior`` advances when ``P(true rate > bar) >= go``.
        go: Posterior probability required under ``posterior`` reading.
        kill: Under ``posterior`` reading, an idea between ``kill`` and ``go`` is neither
            advanced nor stopped: it gets a second round of the same size, and is then advanced
            only if it reaches ``go`` on the pooled evidence. Set ``kill`` equal to ``go`` for a
            single round.
    """

    name: str
    triage_share: float = 1.0
    triage_score: Literal["rice", "ice", "none"] = "rice"
    interviews: int = 12
    pain_bar: float = 0.35
    visitors: int = 600
    signup_bar: float = 0.04
    mvp_users: int = 60
    retention_bar: float = 0.33
    reading: Reading = "posterior"
    go: float = 0.8
    kill: float = 0.3


@dataclass(frozen=True)
class CycleCosts:
    """What each step of the cycle costs, in BRL.

    ``scale_investment`` is what scaling an idea commits. A good idea returns its
    ``value_if_scaled`` net of that; a bad one loses it.
    """

    triage: float = 300.0
    per_interview: float = 400.0
    smoke_fixed: float = 3_000.0
    per_visitor: float = 2.0
    mvp_build: float = 80_000.0
    mvp_fixed: float = 1_000.0
    per_user: float = 150.0
    scale_investment: float = 250_000.0


@dataclass(frozen=True)
class CycleDays:
    """Mean days each step takes. Drawn per idea from a gamma with shape 4 around these."""

    triage: float = 7.0
    interviews: float = 14.0
    smoke: float = 21.0
    build: float = 60.0
    validation: float = 45.0
    scale_decision: float = 14.0

    def as_tuple(self) -> tuple[float, ...]:
        return (
            self.triage,
            self.interviews,
            self.smoke,
            self.build,
            self.validation,
            self.scale_decision,
        )


BASELINE_POLICIES: tuple[GatePolicy, ...] = (
    # Build every captured idea: the counterfactual that prices the existence of gates.
    GatePolicy(
        "Sem gates",
        triage_share=1.0,
        triage_score="none",
        interviews=0,
        visitors=0,
        mvp_users=0,
        reading="point",
    ),
    # How most pipelines run: a gut-feel score cuts the list, small samples read at face value.
    GatePolicy(
        "Intuição",
        triage_share=0.6,
        triage_score="ice",
        interviews=5,
        visitors=100,
        mvp_users=20,
        reading="point",
    ),
    # The textbook upgrade: a structured score, larger samples, a posterior read at 80%.
    GatePolicy("Evidência", triage_share=0.6, triage_score="rice", go=0.8, kill=0.3),
    # More of the same: a harder cut, larger samples, 95% required.
    GatePolicy(
        "Rigor máximo",
        triage_share=0.3,
        triage_score="rice",
        interviews=30,
        visitors=2_000,
        mvp_users=150,
        go=0.95,
        kill=0.3,
    ),
    # No cut on the score, cheap interviews for everything, and a bar whose confidence is set
    # by what each error costs rather than by how rigorous it sounds. Chosen by a grid search on
    # the seed-42 portfolio; reported on an independent one to keep that search honest.
    GatePolicy("Calibrada", triage_share=1.0, interviews=5, go=0.6, kill=0.2),
)


@dataclass
class PolicyRun:
    """One simulated run of a policy over a portfolio."""

    policy: GatePolicy
    ideas: pd.DataFrame
    events: pd.DataFrame
    summary: dict[str, float] = field(default_factory=dict)


def _passes(
    rng: np.random.Generator, true_rate: np.ndarray, n: int, bar: float, policy: GatePolicy
) -> tuple[np.ndarray, np.ndarray]:
    """Draw the evidence for every idea and read it against the bar.

    Returns:
        Whether each idea passes, and how many people it took (for costing). ``n == 0`` passes
        every idea at no cost.
    """
    size = len(true_rate)
    if n == 0:
        return np.ones(size, dtype=bool), np.zeros(size)
    k = rng.binomial(n, true_rate)
    if policy.reading == "point":
        return k / n >= bar, np.full(size, float(n))
    p = prob_above(k, np.full_like(k, n), bar)
    unsure = (p > policy.kill) & (p < policy.go)
    k2 = k + np.where(unsure, rng.binomial(n, true_rate), 0)
    n2 = np.where(unsure, 2 * n, n)
    p2 = np.where(unsure, prob_above(k2, n2, bar), p)
    return p2 >= policy.go, n2.astype(float)


def simulate_policy(
    ideas: pd.DataFrame,
    policy: GatePolicy,
    costs: CycleCosts | None = None,
    days: CycleDays | None = None,
    *,
    seed: int = 0,
) -> PolicyRun:
    """Run every idea through the cycle under ``policy`` and account for what it cost and made.

    Returns:
        A :class:`PolicyRun` with a per-idea frame (furthest stage, spend, outcome), the event log
        in the shape :mod:`funilab.core` reads, and a summary. The summary counts ``false_kills``
        (good ideas stopped at a validation gate) and ``bad_scaled`` (ideas scaled that were not
        good), which only a portfolio with known truth can report.
    """
    costs = costs or CycleCosts()
    days = days or CycleDays()
    rng = np.random.default_rng(seed)
    n = len(ideas)
    stages = IDEA_TO_SOLUTION.stages
    good = ideas["solution_fit"].to_numpy(dtype=bool)

    # Gate 1 - triage by score.
    if policy.triage_score == "none":
        order = rng.permutation(n)
    else:
        score = rice(ideas) if policy.triage_score == "rice" else ice(ideas)
        # Ties broken at random, so a coarse score does not favour capture order.
        order = np.lexsort((rng.random(n), -score.to_numpy()))
    triaged = np.zeros(n, dtype=bool)
    triaged[order[: round(n * policy.triage_share)]] = True

    pain_ok, interviewed = _passes(
        rng, ideas["true_pain_rate"].to_numpy(), policy.interviews, policy.pain_bar, policy
    )
    problem = triaged & pain_ok
    signup_ok, visitors = _passes(
        rng, ideas["true_signup_rate"].to_numpy(), policy.visitors, policy.signup_bar, policy
    )
    solution = problem & signup_ok
    built = solution
    retained_ok, users = _passes(
        rng, ideas["true_retention"].to_numpy(), policy.mvp_users, policy.retention_bar, policy
    )
    validated = built & retained_ok
    scaled = validated
    reached = np.column_stack(
        [np.ones(n, dtype=bool), triaged, problem, solution, built, validated, scaled]
    )

    spend = (
        costs.triage
        + triaged * costs.per_interview * interviewed
        + problem * (costs.smoke_fixed * (visitors > 0) + costs.per_visitor * visitors)
        + built * costs.mvp_build
        + built * (costs.mvp_fixed * (users > 0) + costs.per_user * users)
    )
    value = np.where(
        scaled & good,
        ideas["value_if_scaled"].to_numpy(),
        np.where(scaled, -costs.scale_investment, 0.0),
    )

    step_days = rng.gamma(4.0, np.array(days.as_tuple()) / 4.0, size=(n, len(stages) - 1))
    elapsed = np.cumsum(step_days, axis=1)
    captured = ideas["captured_ts"].to_numpy()
    ts: np.ndarray = np.full((n, len(stages)), np.datetime64("NaT"), dtype="datetime64[ns]")
    ts[:, 0] = captured
    ts[:, 1:] = captured[:, None] + (elapsed * 86_400e9).astype("timedelta64[ns]")
    ts = np.where(reached, ts, np.datetime64("NaT"))

    furthest = reached.sum(axis=1) - 1
    frame = ideas[["idea_id", "source", "solution_fit", "value_if_scaled"]].copy()
    frame["furthest_stage"] = np.array(stages)[furthest]
    frame["spend"] = spend
    frame["value"] = value
    events = (
        pd.DataFrame(ts, columns=list(stages))
        .assign(entity_id=ideas["idea_id"].to_numpy())
        .melt(id_vars="entity_id", var_name="stage", value_name="ts")
        .dropna(subset=["ts"])
        .sort_values(["entity_id", "ts"], ignore_index=True)
    )

    total_spend = float(spend.sum())
    good_scaled = int((scaled & good).sum())
    summary = {
        "ideas": float(n),
        "triaged": float(triaged.sum()),
        "mvps_built": float(built.sum()),
        "scaled": float(scaled.sum()),
        "good_scaled": float(good_scaled),
        "bad_scaled": float((scaled & ~good).sum()),
        "good_in_portfolio": float(good.sum()),
        "false_kills": float((triaged & good & ~validated).sum()),
        "triage_kills_of_good": float((~triaged & good).sum()),
        "spend": total_spend,
        "spend_on_mvps_not_scaled": float((spend * (built & ~scaled)).sum()),
        "cost_per_good_scaled": total_spend / good_scaled if good_scaled else float("inf"),
        "value_scaled": float(value.sum()),
        "net_value": float(value.sum() - total_spend),
    }
    return PolicyRun(policy=policy, ideas=frame, events=events, summary=summary)


def compare_policies(
    ideas: pd.DataFrame,
    policies: tuple[GatePolicy, ...] = BASELINE_POLICIES,
    costs: CycleCosts | None = None,
    *,
    replications: int = 30,
    seed: int = 0,
    metrics: tuple[str, ...] = (
        "mvps_built",
        "good_scaled",
        "bad_scaled",
        "false_kills",
        "spend",
        "cost_per_good_scaled",
        "net_value",
    ),
) -> pd.DataFrame:
    """Each policy replicated with independent evidence draws: mean and 95% interval per metric.

    The interval is the 2.5th to 97.5th percentile across replications - the spread of outcomes a
    team would see running the same policy on the same portfolio with different panels, which is
    the uncertainty a decision about the policy has to live with.
    """
    rows = []
    for index, policy in enumerate(policies):
        runs = pd.DataFrame(
            [
                simulate_policy(ideas, policy, costs, seed=seed * 1_000 + index * 100 + r).summary
                for r in range(replications)
            ]
        )
        for metric in metrics:
            values = runs[metric].replace([np.inf], np.nan)
            rows.append(
                {
                    "policy": policy.name,
                    "metric": metric,
                    "mean": float(values.mean()),
                    "low": float(values.quantile(0.025)),
                    "high": float(values.quantile(0.975)),
                }
            )
    return pd.DataFrame(rows).set_index(["policy", "metric"])


def paired_difference(
    ideas: pd.DataFrame,
    a: GatePolicy,
    b: GatePolicy,
    costs: CycleCosts | None = None,
    *,
    metric: str = "net_value",
    replications: int = 60,
    seed: int = 0,
) -> dict[str, float]:
    """``a`` minus ``b`` on one metric, both policies run on the same draws in each replication.

    Comparing two policies' separate ranges answers the wrong question: the ranges can overlap even
    when one policy beats the other in every single run, because most of each range is the luck
    both share - which ideas happened to impress their interviewees. Running both on the same seed
    (common random numbers) cancels that shared luck, so the spread of the *difference* is what is
    left to decide on.

    Returns:
        ``mean``, ``low`` and ``high`` (2.5th and 97.5th percentiles of the per-replication
        difference), ``share_positive`` (how often ``a`` came out ahead) and ``replications``.
    """
    differences = np.array(
        [
            simulate_policy(ideas, a, costs, seed=seed * 1_000 + r).summary[metric]
            - simulate_policy(ideas, b, costs, seed=seed * 1_000 + r).summary[metric]
            for r in range(replications)
        ]
    )
    return {
        "mean": float(differences.mean()),
        "low": float(np.quantile(differences, 0.025)),
        "high": float(np.quantile(differences, 0.975)),
        "share_positive": float((differences > 0).mean()),
        "replications": float(replications),
    }
