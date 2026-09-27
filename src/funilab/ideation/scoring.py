"""Prioritisation scores and how to test them against what they were meant to predict.

RICE (reach x impact x confidence / effort) and ICE (impact x confidence x ease) are the two
scorecards most idea pipelines use at triage. Both are fine as a way to structure a conversation.
Neither has been validated as a predictor on any particular portfolio, and the only way to find
out whether one works on *yours* is to compare it with outcomes, which is what the rest of this
module does.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def rice(ideas: pd.DataFrame) -> pd.Series:
    """Reach x impact x confidence / effort."""
    return (ideas["reach"] * ideas["impact"] * ideas["confidence"] / ideas["effort"]).rename("rice")


def ice(ideas: pd.DataFrame) -> pd.Series:
    """Impact x confidence x ease, each put on a 1-10 scale.

    Impact is carried on the RICE scale (0.25 to 3) and confidence as a share, so both are
    rescaled rather than asking the same team for a second set of guesses.
    """
    impact = ideas["impact"] / 3 * 10
    confidence = ideas["confidence"] * 10
    return (impact * confidence * ideas["ease"]).rename("ice")


def score_table(ideas: pd.DataFrame) -> pd.DataFrame:
    """Both scores and both ranks, indexed like ``ideas``."""
    table = pd.concat([rice(ideas), ice(ideas)], axis=1)
    table["rank_rice"] = table["rice"].rank(ascending=False, method="first").astype(int)
    table["rank_ice"] = table["ice"].rank(ascending=False, method="first").astype(int)
    return table


def top_overlap(a: pd.Series, b: pd.Series, share: float) -> float:
    """Share of the top ``share`` by score ``a`` that is also in the top ``share`` by ``b``."""
    k = max(1, round(len(a) * share))
    top_a = set(a.nlargest(k).index)
    top_b = set(b.nlargest(k).index)
    return len(top_a & top_b) / k


def spearman(a: pd.Series, b: pd.Series) -> float:
    """Rank correlation, computed on average ranks so ties are handled."""
    return float(np.corrcoef(a.rank(), b.rank())[0, 1])


def precision_at(score: pd.Series, truth: pd.Series, share: float) -> float:
    """Share of genuinely good ideas among the top ``share`` of ideas by ``score``."""
    k = max(1, round(len(score) * share))
    return float(truth.loc[score.nlargest(k).index].mean())


def score_validity(ideas: pd.DataFrame, *, truth: str = "solution_fit") -> pd.DataFrame:
    """How well each score predicts the outcome it is used to anticipate.

    Returns:
        One row per score with its rank correlation to realisable value (value if the idea is
        good, zero otherwise), the share of good ideas in its top 20% and top 50%, and the base
        rate for comparison - a score whose top 20% is no richer in good ideas than the base rate
        is sorting by noise.
    """
    good = ideas[truth].astype(bool)
    realisable = ideas["value_if_scaled"].where(good, 0.0)
    rows = []
    for name, score in (("rice", rice(ideas)), ("ice", ice(ideas))):
        rows.append(
            {
                "score": name,
                "spearman_with_value": spearman(score, realisable),
                "precision_top20": precision_at(score, good, 0.20),
                "precision_top50": precision_at(score, good, 0.50),
                "base_rate": float(good.mean()),
            }
        )
    return pd.DataFrame(rows).set_index("score")
