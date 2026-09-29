from __future__ import annotations

import pandas as pd
import pytest

from funilab.ideation import (
    BASELINE_POLICIES,
    GatePolicy,
    break_even_payoff,
    compare_policies,
    ice,
    paired_difference,
    precision_at,
    rice,
    score_validity,
    simulate_policy,
    spearman,
    stage_value,
    top_overlap,
)
from funilab.synth import SynthConfig, generate_ideas


@pytest.fixture(scope="module")
def ideas() -> pd.DataFrame:
    return generate_ideas(SynthConfig(days=90)).ideas


def test_rice_and_ice_by_hand() -> None:
    card = pd.DataFrame(
        {"reach": [8.0], "impact": [2.0], "confidence": [0.5], "effort": [4.0], "ease": [7.0]}
    )
    assert rice(card).iloc[0] == pytest.approx(8 * 2 * 0.5 / 4)
    assert ice(card).iloc[0] == pytest.approx((2 / 3 * 10) * 5 * 7)


def test_overlap_precision_and_rank_correlation() -> None:
    a = pd.Series([4.0, 3.0, 2.0, 1.0])
    b = pd.Series([1.0, 2.0, 3.0, 4.0])
    assert top_overlap(a, a, 0.5) == 1.0
    assert top_overlap(a, b, 0.5) == 0.0
    assert spearman(a, b) == pytest.approx(-1.0)
    truth = pd.Series([True, False, True, False])
    assert precision_at(a, truth, 0.5) == 0.5


def test_score_validity_shape(ideas: pd.DataFrame) -> None:
    table = score_validity(ideas)
    assert list(table.index) == ["rice", "ice"]
    assert (table["base_rate"] == ideas["solution_fit"].mean()).all()


def test_without_gates_everything_is_built_and_scaled(ideas: pd.DataFrame) -> None:
    run = simulate_policy(ideas, BASELINE_POLICIES[0])
    assert run.summary["scaled"] == len(ideas)
    assert run.summary["bad_scaled"] == (~ideas["solution_fit"]).sum()
    assert run.summary["false_kills"] == 0


def test_accounting_identities(ideas: pd.DataFrame) -> None:
    run = simulate_policy(ideas, GatePolicy("x", triage_share=0.5), seed=3)
    s = run.summary
    assert s["good_scaled"] + s["bad_scaled"] == s["scaled"]
    assert s["good_scaled"] + s["false_kills"] + s["triage_kills_of_good"] == s["good_in_portfolio"]
    assert s["spend"] == pytest.approx(run.ideas["spend"].sum())
    assert s["net_value"] == pytest.approx(run.ideas["value"].sum() - run.ideas["spend"].sum())
    assert s["triaged"] == round(len(ideas) * 0.5)


def test_simulation_is_reproducible(ideas: pd.DataFrame) -> None:
    policy = BASELINE_POLICIES[2]
    assert (
        simulate_policy(ideas, policy, seed=7).summary
        == simulate_policy(ideas, policy, seed=7).summary
    )


def test_events_are_monotone_in_time(ideas: pd.DataFrame) -> None:
    run = simulate_policy(ideas, BASELINE_POLICIES[-1], seed=1)
    ordered = run.events.sort_values(["entity_id", "ts"])
    assert ordered.groupby("entity_id")["ts"].apply(lambda s: s.is_monotonic_increasing).all()


def test_compare_policies_reports_an_interval(ideas: pd.DataFrame) -> None:
    table = compare_policies(ideas, BASELINE_POLICIES[1:3], replications=4, metrics=("spend",))
    assert (table["low"] <= table["mean"]).all() and (table["mean"] <= table["high"]).all()


def test_stage_value_by_hand() -> None:
    # Two tests: 50% at cost 10, then 20% at cost 100, payoff 1000.
    table = stage_value(["s1", "s2"], [0.5, 0.2], [10.0, 100.0], 1000.0)
    assert table.loc["s2", "expected_value"] == pytest.approx(-100 + 0.2 * 1000)
    assert table.loc["s1", "expected_value"] == pytest.approx(-10 + 0.5 * 100)
    assert table.loc["s1", "p_success"] == pytest.approx(0.1)
    assert table.loc["s1", "cost_to_go"] == pytest.approx(10 + 0.5 * 100)
    assert break_even_payoff([0.5, 0.2], [10.0, 100.0]) == pytest.approx(60 / 0.1)


def test_stage_value_validates_lengths() -> None:
    with pytest.raises(ValueError):
        stage_value(["a"], [0.5, 0.5], [1.0], 10.0)


def test_paired_difference_of_a_policy_with_itself_is_exactly_zero(ideas: pd.DataFrame) -> None:
    policy = BASELINE_POLICIES[2]
    result = paired_difference(ideas, policy, policy, replications=5)
    assert result["mean"] == result["low"] == result["high"] == 0.0
    assert result["share_positive"] == 0.0


def test_paired_difference_is_antisymmetric(ideas: pd.DataFrame) -> None:
    a, b = BASELINE_POLICIES[1], BASELINE_POLICIES[4]
    ab = paired_difference(ideas, a, b, replications=5)
    ba = paired_difference(ideas, b, a, replications=5)
    assert ab["mean"] == pytest.approx(-ba["mean"])
    assert ab["low"] == pytest.approx(-ba["high"])
