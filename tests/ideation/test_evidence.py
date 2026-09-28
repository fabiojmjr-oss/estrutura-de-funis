from __future__ import annotations

import numpy as np
import pytest

from funilab.ideation import beta_cdf, decide, neutral_prior, prob_above, sample_size


@pytest.mark.parametrize("x", [0.05, 0.3, 0.5, 0.9])
def test_beta_cdf_closed_forms(x: float) -> None:
    assert float(beta_cdf(x, 1, 1)) == pytest.approx(x)
    assert float(beta_cdf(x, 2, 1)) == pytest.approx(x**2)
    assert float(beta_cdf(x, 1, 3)) == pytest.approx(1 - (1 - x) ** 3)
    # Beta(2, 2): 3x^2 - 2x^3
    assert float(beta_cdf(x, 2, 2)) == pytest.approx(3 * x**2 - 2 * x**3)


def test_beta_cdf_symmetry_and_edges() -> None:
    assert float(beta_cdf(0.5, 7.3, 7.3)) == pytest.approx(0.5)
    assert float(beta_cdf(0.3, 4, 9)) == pytest.approx(1 - float(beta_cdf(0.7, 9, 4)))
    assert float(beta_cdf(0.0, 2, 3)) == 0.0
    assert float(beta_cdf(1.0, 2, 3)) == 1.0


def test_beta_cdf_large_counts_agree_with_the_normal_approximation() -> None:
    # Beta(501, 501) is close to normal with sd sqrt(0.25 / 1003).
    sd = np.sqrt(0.25 / 1003)
    assert float(beta_cdf(0.5 + sd, 501, 501)) == pytest.approx(0.8413, abs=2e-3)


@pytest.mark.parametrize("threshold", [0.02, 0.04, 0.35, 0.8])
def test_neutral_prior_gives_even_odds_before_any_evidence(threshold: float) -> None:
    a, b = neutral_prior(threshold)
    assert a + b == pytest.approx(2.0)
    assert float(prob_above(0, 0, threshold)) == pytest.approx(0.5, abs=1e-9)


def test_neutral_prior_rejects_degenerate_bars() -> None:
    with pytest.raises(ValueError):
        neutral_prior(0.0)


def test_uniform_prior_is_not_neutral_at_a_low_bar() -> None:
    """The defect the neutral default exists for: two visitors who leave, and a 'pass'."""
    assert float(prob_above(0, 2, 0.04, prior=(1.0, 1.0))) > 0.8
    assert float(prob_above(0, 2, 0.04)) < 0.5


def test_more_of_the_same_evidence_is_more_certain() -> None:
    p = [float(prob_above(4 * m, 10 * m, 0.35)) for m in (1, 2, 4, 8)]
    assert p == sorted(p)


def test_decide_three_outcomes() -> None:
    out = decide(np.array([18, 2, 5]), np.array([20, 20, 12]), 0.35)
    assert out.tolist() == ["go", "kill", "more evidence"]
    with pytest.raises(ValueError):
        decide(1, 2, 0.5, go=0.3, kill=0.5)


def test_sample_size_grows_as_the_rate_nears_the_bar() -> None:
    far = sample_size(0.07, 0.04)
    near = sample_size(0.045, 0.04)
    assert near > 10 * far
    n = sample_size(0.07, 0.04)
    assert float(prob_above(n * 0.07, n, 0.04)) >= 0.8
    assert float(prob_above((n - 1) * 0.07, n - 1, 0.04)) < 0.8


def test_sample_size_refuses_an_idea_exactly_at_the_bar() -> None:
    with pytest.raises(ValueError):
        sample_size(0.04, 0.04)
