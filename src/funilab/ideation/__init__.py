"""The idea-to-solution cycle: capture, triage, problem, solution, MVP, validation, scale.

This is the funnel the package is built around, and the one with the least data behind the
decisions taken in it. Four pieces:

:mod:`~funilab.ideation.scoring`
    RICE and ICE, and :func:`score_validity` to test whether either predicts anything on a given
    portfolio.
:mod:`~funilab.ideation.evidence`
    Reading a small experiment against a bar that was set in advance: :func:`prob_above`,
    :func:`decide` and :func:`sample_size`.
:mod:`~funilab.ideation.gates`
    Whole gate policies, simulated on a portfolio with known truth: :func:`simulate_policy` and
    :func:`compare_policies`.
:mod:`~funilab.ideation.economics`
    The expected value of an idea at each stage: :func:`stage_value`.

The playbook that puts these to work, with templates for every gate, is
``docs/ciclo-ideia-mvp.md``.
"""

from .economics import break_even_payoff, stage_value
from .evidence import beta_cdf, decide, neutral_prior, prob_above, sample_size
from .gates import (
    BASELINE_POLICIES,
    CycleCosts,
    CycleDays,
    GatePolicy,
    PolicyRun,
    compare_policies,
    paired_difference,
    simulate_policy,
)
from .scoring import ice, precision_at, rice, score_table, score_validity, spearman, top_overlap
from .stages import IDEA_TO_SOLUTION

__all__ = [
    "BASELINE_POLICIES",
    "IDEA_TO_SOLUTION",
    "CycleCosts",
    "CycleDays",
    "GatePolicy",
    "PolicyRun",
    "beta_cdf",
    "break_even_payoff",
    "compare_policies",
    "decide",
    "ice",
    "neutral_prior",
    "paired_difference",
    "precision_at",
    "prob_above",
    "rice",
    "sample_size",
    "score_table",
    "score_validity",
    "simulate_policy",
    "spearman",
    "stage_value",
    "top_overlap",
]
