"""Evidence at a gate: how sure are we that the true rate clears the bar?

Every gate from problem validation onwards reduces to the same question. Some number of people
were exposed - interviewed, shown a landing page, given the MVP - and some of them responded.
The gate has a threshold on the *true* rate, and a point estimate from a small sample says very
little about it: 2 of 5 interviewees is 40%, and it is also entirely consistent with 15%.

The functions here use a Beta posterior, so the gate question becomes a probability that can be
set in advance: advance when ``P(true rate > threshold) >= go``, stop when it is below ``kill``,
and collect more evidence in between. No SciPy: the regularised incomplete beta function is
computed by continued fraction, vectorised, and tested against closed forms.

The default prior is **neutral at the bar**: a Beta with its median on the threshold and the
weight of two observations. Before any evidence it gives an idea exactly even odds of clearing
the bar, which is what "we do not know yet" means. The uniform prior that textbooks default to
is not neutral here: against a 4% sign-up bar it starts at 96% confidence that the idea clears
it, and two visitors who both leave are enough to "pass" at 80%. That defect was found by this
module's own example, and it is why the default is what it is.
"""

from __future__ import annotations

import math
from functools import lru_cache
from typing import Literal

import numpy as np

Decision = Literal["go", "kill", "more evidence"]
Prior = tuple[float, float] | None
NEUTRAL_WEIGHT = 2.0

_FPMIN = 1e-300
_lgamma = np.frompyfunc(math.lgamma, 1, 1)


def _betacf(a: np.ndarray, b: np.ndarray, x: np.ndarray, iterations: int = 300) -> np.ndarray:
    """Continued fraction for the incomplete beta function (modified Lentz).

    Stops as soon as every element has converged to machine precision.
    """
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = np.ones_like(x)
    d = 1.0 - qab * x / qap
    d = np.where(np.abs(d) < _FPMIN, _FPMIN, d)
    d = 1.0 / d
    h = d.copy()
    for m in range(1, iterations + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = np.where(np.abs(d) < _FPMIN, _FPMIN, d)
        c = 1.0 + aa / c
        c = np.where(np.abs(c) < _FPMIN, _FPMIN, c)
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = np.where(np.abs(d) < _FPMIN, _FPMIN, d)
        c = 1.0 + aa / c
        c = np.where(np.abs(c) < _FPMIN, _FPMIN, c)
        d = 1.0 / d
        delta = d * c
        h *= delta
        if np.all(np.abs(delta - 1.0) < 3e-16):
            break
    return h


def beta_cdf(x: float | np.ndarray, a: float | np.ndarray, b: float | np.ndarray) -> np.ndarray:
    """Regularised incomplete beta function: ``P(X <= x)`` for ``X ~ Beta(a, b)``."""
    xs, as_, bs = np.broadcast_arrays(
        np.asarray(x, dtype=float), np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    )
    xs = np.clip(xs, 0.0, 1.0)
    out = np.where(xs <= 0.0, 0.0, 1.0)
    inner = np.asarray((xs > 0.0) & (xs < 1.0))
    if not inner.any():
        return out
    xi, ai, bi = xs[inner], as_[inner], bs[inner]
    log_front = (
        np.asarray(_lgamma(ai + bi), dtype=float)
        - np.asarray(_lgamma(ai), dtype=float)
        - np.asarray(_lgamma(bi), dtype=float)
        + ai * np.log(xi)
        + bi * np.log1p(-xi)
    )
    front = np.exp(log_front)
    direct = xi < (ai + 1.0) / (ai + bi + 2.0)
    value = np.where(
        direct,
        front * _betacf(ai, bi, xi) / ai,
        1.0 - front * _betacf(bi, ai, 1.0 - xi) / bi,
    )
    out = out.astype(float)
    out[inner] = value
    return out


@lru_cache(maxsize=256)
def neutral_prior(threshold: float, weight: float = NEUTRAL_WEIGHT) -> tuple[float, float]:
    """Beta ``(a, b)`` with ``a + b = weight`` whose median sits exactly on ``threshold``.

    The median, not the mean: a Beta with its mean on a low bar is so skewed that most of its
    mass sits below the bar, and one visitor who leaves is then enough to kill an idea. With the
    median on the bar the prior gives exactly even odds of clearing it, which is what "no
    evidence yet" has to mean. Solved by bisection, since the median has no closed form.
    """
    if not 0 < threshold < 1:
        raise ValueError("threshold must be strictly between 0 and 1")
    low, high = 1e-9, weight - 1e-9
    for _ in range(80):
        a = (low + high) / 2
        # The CDF at the bar falls as a grows, so move towards the side that gives one half.
        if float(beta_cdf(threshold, a, weight - a)) > 0.5:
            low = a
        else:
            high = a
    a = (low + high) / 2
    return a, weight - a


def prob_above(
    successes: int | np.ndarray,
    trials: int | np.ndarray,
    threshold: float,
    prior: Prior = None,
) -> np.ndarray:
    """Posterior probability that the true rate exceeds ``threshold``.

    Args:
        successes: Respondents who showed the behaviour (confirmed the pain, signed up, stayed).
        trials: People exposed.
        threshold: The bar the true rate has to clear.
        prior: Beta ``(a, b)``. ``None`` (the default) is :func:`neutral_prior` at the threshold.
            A prior fitted to past experiments is the honest way to use a portfolio's history,
            and it is an argument rather than a constant for that reason.
    """
    prior = prior if prior is not None else neutral_prior(threshold)
    k = np.asarray(successes, dtype=float)
    n = np.asarray(trials, dtype=float)
    return 1.0 - beta_cdf(threshold, prior[0] + k, prior[1] + n - k)


def decide(
    successes: int | np.ndarray,
    trials: int | np.ndarray,
    threshold: float,
    *,
    go: float = 0.8,
    kill: float = 0.2,
    prior: Prior = None,
) -> np.ndarray:
    """``go``, ``kill`` or ``more evidence`` from the posterior probability of clearing the bar."""
    if not 0 <= kill < go <= 1:
        raise ValueError("need 0 <= kill < go <= 1")
    p = prob_above(successes, trials, threshold, prior)
    return np.where(p >= go, "go", np.where(p <= kill, "kill", "more evidence"))


def sample_size(
    expected_rate: float,
    threshold: float,
    *,
    go: float = 0.8,
    prior: Prior = None,
    max_n: int = 100_000,
) -> int:
    """Smallest sample at which an idea performing at ``expected_rate`` reaches a decision.

    The sample is assumed to come out exactly at the expected rate (fractional successes are
    fine for a Beta), so this is the size at which a *typical* result decides, not a guarantee.
    If ``expected_rate`` is above the threshold the decision sought is ``go``; below it, ``kill``
    at probability ``1 - go``. The closer the expected rate sits to the bar, the larger the
    sample - which is the argument for setting the bar *before* seeing the result: a bar set
    after the fact always sits where the sample can clear it.
    """
    if expected_rate == threshold:
        raise ValueError("an idea performing exactly at the bar never reaches a decision")
    above = expected_rate > threshold

    def decided(n: np.ndarray) -> np.ndarray:
        p = prob_above(n * expected_rate, n, threshold, prior)
        return p >= go if above else p <= 1 - go

    candidates = np.unique(np.round(np.geomspace(1, max_n, 600)).astype(int))
    hits = decided(candidates.astype(float))
    if not hits.any():
        raise ValueError(f"no sample up to {max_n} reaches a decision")
    first_hit = int(np.argmax(hits))
    upper = int(candidates[first_hit])
    lower = int(candidates[max(first_hit - 1, 0)])
    exact = np.arange(lower, upper + 1)
    return int(exact[np.argmax(decided(exact.astype(float)))])
