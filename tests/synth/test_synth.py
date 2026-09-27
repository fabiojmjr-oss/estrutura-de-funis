from __future__ import annotations

import pandas as pd

from funilab.core import funnel_table
from funilab.marketing import MARKETING
from funilab.sales import PIPELINE
from funilab.synth import (
    SynthConfig,
    generate_ideas,
    generate_management,
    generate_marketing,
    generate_sales,
    generate_supply,
)

SMALL = SynthConfig(days=60, history_days=30)


def test_reproducible_from_the_seed() -> None:
    a = generate_sales(SMALL).opportunities
    b = generate_sales(SMALL).opportunities
    pd.testing.assert_frame_equal(a, b)


def test_a_different_seed_differs() -> None:
    a = generate_ideas(SMALL).ideas
    b = generate_ideas(SynthConfig(days=60, seed=7)).ideas
    assert len(a) != len(b) or not a["value_if_scaled"].equals(b["value_if_scaled"])


def test_nothing_is_observed_after_as_of() -> None:
    for events in (
        generate_marketing(SMALL).events,
        generate_sales(SMALL).events,
        generate_supply(SMALL).events,
        generate_management(SMALL).events,
    ):
        assert events["ts"].max() <= SMALL.as_of


def test_marketing_funnel_narrows_and_spend_is_paid_only() -> None:
    data = generate_marketing(SMALL)
    table = funnel_table(data.events, MARKETING)
    assert table["entered"].is_monotonic_decreasing
    assert set(data.spend["channel"]) == {"Busca paga", "Social pago", "Eventos"}
    first = data.touches.loc[data.touches["touch"] == 0].set_index("lead_id")["channel"]
    source = data.leads.set_index("lead_id")["channel"]
    assert (first.reindex(source.index) == source).all()


def test_sales_open_deals_have_no_close_date_and_known_eventual_outcome() -> None:
    deals = generate_sales(SMALL).opportunities
    open_deals = deals[deals["status"] == "open"]
    assert open_deals["close_ts"].isna().all()
    assert set(open_deals["eventual_status"]) <= {"won", "lost"}
    closed = deals[deals["status"] != "open"]
    assert (closed["status"] == closed["eventual_status"]).all()
    assert set(deals["entry_stage"]) == {PIPELINE.stages[0], "Proposta"}


def test_supply_attempts_are_consistent() -> None:
    data = generate_supply(SMALL)
    assert (data.attempts["attempts"] >= 1).all()
    assert (~data.attempts["first_pass"] | (data.attempts["attempts"] == 1)).all()
    assert (data.attempts.loc[data.attempts["first_pass"], "passed"]).all()


def test_management_statuses_are_exclusive() -> None:
    initiatives = generate_management(SMALL).initiatives
    assert set(initiatives["status"]) <= {"measured", "stopped", "in_flight"}
    measured = initiatives["status"] == "measured"
    assert initiatives.loc[measured, "realised_benefit"].notna().all()
    assert initiatives.loc[~measured, "realised_benefit"].isna().all()


def test_ideas_latent_structure() -> None:
    ideas = generate_ideas(SMALL).ideas
    assert (~ideas["solution_fit"] | ideas["problem_real"]).all()
    assert ideas["true_signup_rate"].between(0, 1).all()
