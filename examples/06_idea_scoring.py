"""Does the triage score predict anything, and how much evidence does a gate need?

Run:
    python examples/06_idea_scoring.py
"""

from __future__ import annotations

import pandas as pd

from funilab.ideation import ice, prob_above, rice, sample_size, score_validity, top_overlap
from funilab.synth import SynthConfig, generate_ideas


def main() -> None:
    pd.set_option("display.width", 160)
    ideas = generate_ideas(SynthConfig(seed=2026)).ideas  # the portfolio of example 07

    print("1. Two scores against the outcome they are meant to anticipate")
    print(score_validity(ideas).round(3).to_string())
    print(
        f"\n   RICE and ICE share {top_overlap(rice(ideas), ice(ideas), 0.2):.0%} of their top 20%."
        "\n   The better of the two lifts the share of good ideas in its top fifth from the base"
        "\n   rate by less than ten points. A score is a conversation aid, not a filter."
    )

    print("\n2. What a small sample says about a bar")
    for k, n in ((2, 5), (4, 10), (8, 20)):
        p = float(prob_above(k, n, 0.35))
        print(f"   {k:>2} of {n:>2} interviewees confirm the pain: P(true rate > 35%) = {p:.2f}")
    print(
        "\n   40% observed in every row, so a point reading passes all three against a 35% bar."
        "\n   None of them reaches 80% confidence that the true rate clears it."
    )

    print("\n3. Sample size to reach a decision at 80%")
    for rate, bar, label in (
        (0.07, 0.04, "smoke test, good idea"),
        (0.02, 0.04, "smoke test, weak idea"),
        (0.045, 0.04, "smoke test, borderline"),
        (0.45, 0.33, "MVP retention, good"),
    ):
        print(f"   {label:<24} true {rate:.1%} vs bar {bar:.0%}: n = {sample_size(rate, bar)}")


if __name__ == "__main__":
    main()
