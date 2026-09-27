"""Every figure quoted in the README, asserted against the code that produces it.

A README is documentation until it carries numbers, at which point it is a claim. These tests make
the claims fail loudly rather than drift: any change to a generator, a convention or a policy that
moves one of these figures breaks the build and forces the text to move with it.

They use the default :class:`SynthConfig` (seed 42) and, for the gate policies, the independent
seed-2026 portfolio the README reports on. The policy replications take the longest, so the whole
module is marked ``slow``.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pandas as pd
import pytest

from funilab.core import conversion_sensitivity, funnel_table, lever_table
from funilab.ideation import (
    compare_policies,
    prob_above,
    score_validity,
)
from funilab.management import EXECUTION, benefit_bridge, execution_flow
from funilab.marketing import MARKETING, cac_by_attribution, cac_table
from funilab.sales import CRM_DEFAULT_PROBABILITY, PIPELINE, forecast_table, win_rates
from funilab.supply import FULFILMENT, hidden_factory, perfect_order, yield_table
from funilab.synth import (
    SynthConfig,
    generate_ideas,
    generate_management,
    generate_marketing,
    generate_sales,
    generate_supply,
)

pytestmark = pytest.mark.slow

ROOT = Path(__file__).resolve().parents[1]
CONFIG = SynthConfig()
WINDOW = pd.Timedelta(days=120)
TOL = 5e-5


@pytest.fixture(scope="module")
def marketing():  # type: ignore[no-untyped-def]
    return generate_marketing(CONFIG)


@pytest.fixture(scope="module")
def sales():  # type: ignore[no-untyped-def]
    return generate_sales(CONFIG)


@pytest.fixture(scope="module")
def policies() -> pd.DataFrame:
    ideas = generate_ideas(SynthConfig(seed=2026)).ideas
    return compare_policies(
        ideas,
        replications=30,
        metrics=("mvps_built", "good_scaled", "bad_scaled", "triage_kills_of_good", "net_value"),
    )


# 1 --------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("start", "end", "expected"),
    [
        ("2025-07-01", "2025-09-30", (0.0233, 0.0245, 0.0241, 0.0268)),
        ("2025-10-01", "2025-12-31", (0.0246, 0.0123, 0.0123, None)),
    ],
)
def test_finding_1_quarter_conventions(marketing, start, end, expected) -> None:  # type: ignore[no-untyped-def]
    table = conversion_sensitivity(
        marketing.events,
        MARKETING,
        start=pd.Timestamp(start),
        end=pd.Timestamp(end),
        window=WINDOW,
        as_of=CONFIG.as_of,
    )["end_to_end"]
    period, cohort_all, cohort_window, matured = expected
    assert table["period"] == pytest.approx(period, abs=TOL)
    assert table["cohort_all"] == pytest.approx(cohort_all, abs=TOL)
    assert table["cohort_window"] == pytest.approx(cohort_window, abs=TOL)
    if matured is None:
        assert pd.isna(table["cohort_matured"])
    else:
        assert table["cohort_matured"] == pytest.approx(matured, abs=TOL)


# 2 --------------------------------------------------------------------------------------------


def test_finding_2_levers(marketing) -> None:  # type: ignore[no-untyped-def]
    matured = funnel_table(
        marketing.events, MARKETING, window=WINDOW, as_of=CONFIG.as_of, mature_only=True
    )
    rates = matured["step_rate"].dropna()
    assert rates.round(3).tolist() == [0.368, 0.320, 0.224]
    table = lever_table(rates, 10_000)
    assert table.loc["Cliente", "gain_absolute_pct"] == pytest.approx(0.0447, abs=TOL)
    assert table.loc["MQL", "gain_absolute_pct"] == pytest.approx(0.0272, abs=TOL)
    gains = table["gain_relative"]
    assert gains.max() - gains.min() == pytest.approx(0.0, abs=1e-9)


# 3 --------------------------------------------------------------------------------------------


def test_finding_3_cac_and_attribution(marketing) -> None:  # type: ignore[no-untyped-def]
    start, end = CONFIG.start_ts, CONFIG.as_of
    table = cac_table(marketing.leads, marketing.spend, start=start, end=end)
    assert table.loc["paid (total)", "spend"] == pytest.approx(2_026_686, abs=1)
    assert table.loc["paid (total)", "customers"] == 472
    assert table.loc["blended (total)", "customers"] == 789
    assert round(table.loc["blended (total)", "cac"]) == 2_569
    assert round(table.loc["paid (total)", "cac"]) == 4_294
    assert 1 - table.loc["blended (total)", "cac"] / table.loc["paid (total)", "cac"] == (
        pytest.approx(0.40, abs=0.005)
    )

    customers = marketing.leads.loc[marketing.leads["Cliente"].between(start, end), "lead_id"]
    in_period = marketing.spend.loc[marketing.spend["month"].between(start, end)]
    cac = cac_by_attribution(
        marketing.touches, customers, in_period.groupby("channel")["spend"].sum()
    )
    assert round(cac.loc["Eventos", "cac_first"]) == 3_161
    assert round(cac.loc["Eventos", "cac_last"]) == 9_238
    assert round(cac.loc["Busca paga", "cac_first"]) == 3_559
    assert round(cac.loc["Busca paga", "cac_last"]) == 1_957
    assert round(cac.loc["Social pago", "cac_first"]) == 8_189
    assert round(cac.loc["Social pago", "cac_last"]) == 4_649
    assert (cac.loc["Eventos", "rank_first"], cac.loc["Eventos", "rank_last"]) == (1, 3)
    assert cac.loc["Eventos", "cac_last"] / cac.loc["Eventos", "cac_first"] == pytest.approx(
        2.9, abs=0.05
    )


# 4 and 5 --------------------------------------------------------------------------------------


def test_finding_4_skipped_stages_and_win_rates(sales) -> None:  # type: ignore[no-untyped-def]
    literal = funnel_table(sales.events, PIPELINE, skipped="literal")
    assert literal.loc["Proposta", "entered"] == 1_842
    assert literal.loc["Qualificação", "entered"] == 1_682
    assert literal.loc["Proposta", "step_rate"] == pytest.approx(1.095, abs=5e-4)
    inferred = funnel_table(sales.events, PIPELINE)
    assert inferred.loc["Proposta", "step_rate"] == pytest.approx(0.754, abs=5e-4)
    rates = win_rates(sales.opportunities)["win_rate"]
    assert rates["count_closed"] == pytest.approx(0.215, abs=5e-4)
    assert rates["value_closed"] == pytest.approx(0.156, abs=5e-4)


def test_finding_5_forecast(sales) -> None:  # type: ignore[no-untyped-def]
    deals = sales.opportunities
    open_deals = deals[deals["status"] == "open"]
    assert len(open_deals) == 333
    assert open_deals["amount"].sum() == pytest.approx(22.06e6, rel=1e-3)
    table = forecast_table(sales.events, deals, PIPELINE, CONFIG.as_of, CRM_DEFAULT_PROBABILITY)
    assert table.loc["crm_default", "forecast"] == pytest.approx(7.97e6, rel=1e-3)
    assert table.loc["historical", "forecast"] == pytest.approx(8.19e6, rel=1e-3)
    assert table.loc["historical_fresh", "forecast"] == pytest.approx(5.38e6, rel=1e-3)
    assert table["error"].round(3).tolist() == [0.458, 0.499, -0.015]
    assert table.attrs["stale_deals"] == 83
    assert table.attrs["stale_amount"] == pytest.approx(7.8e6, rel=5e-3)


def test_finding_5_stale_deals_win_rarely(sales) -> None:  # type: ignore[no-untyped-def]
    from funilab.sales import stage_age, stale_threshold

    deals = sales.opportunities
    open_deals = deals[deals["status"] == "open"]
    limits = stale_threshold(sales.events, deals, PIPELINE)
    stale = stage_age(deals, CONFIG.as_of) > open_deals["current_stage"].map(limits)
    won = open_deals["eventual_status"] == "won"
    assert won[stale].mean() == pytest.approx(0.048, abs=5e-4)
    assert won[~stale].mean() == pytest.approx(0.436, abs=5e-4)


# 6 --------------------------------------------------------------------------------------------


def test_finding_6_hidden_factory() -> None:
    data = generate_supply(CONFIG)
    table = yield_table(data.attempts, FULFILMENT.stages[1:])
    assert table["first_pass_yield"].round(3).tolist() == [
        0.929,
        0.950,
        0.965,
        0.975,
        0.918,
        0.762,
    ]
    assert table["final_yield"].round(3).tolist() == [0.998, 0.999, 0.999, 0.999, 0.998, 0.993]
    assert hidden_factory(data.attempts, data.orders)["orders_reworked_share"] == pytest.approx(
        0.235, abs=5e-4
    )
    perfect = perfect_order(data.orders)["rate"]
    assert perfect["product (assumes independence)"] == pytest.approx(0.8586, abs=TOL)
    assert perfect["joint (measured)"] == pytest.approx(0.8585, abs=TOL)


# 7 and 8 --------------------------------------------------------------------------------------


def test_finding_7_benefit_bridge() -> None:
    initiatives = generate_management(CONFIG).initiatives
    cohort = initiatives[initiatives["proposed_ts"] < CONFIG.start_ts]
    bridge = benefit_bridge(cohort, EXECUTION)["benefit"] / 1e6
    assert round(bridge["announced"], 1) == 134.4
    assert round(bridge["stopped before Aprovada"], 1) == -59.5
    stopped_mid = bridge[
        ["stopped before Financiada", "stopped before Em execução", "stopped before Entregue"]
    ].sum()
    assert round(stopped_mid, 1) == -38.7
    assert round(stopped_mid / bridge["announced"], 3) == -0.288
    assert round(bridge["stopped before Benefício medido"], 1) == -14.6
    assert round(bridge["still in flight"], 1) == -2.9
    assert round(bridge["under-delivered"], 1) == -4.4
    assert round(bridge["realised"], 1) == 14.3
    assert round(bridge["realised"] / bridge["announced"], 3) == 0.106


def test_finding_8_littles_law() -> None:
    initiatives = generate_management(CONFIG).initiatives
    half = CONFIG.start_ts + pd.Timedelta(days=182)
    first = execution_flow(initiatives, window_start=CONFIG.start_ts, window_end=half)
    second = execution_flow(initiatives, window_start=half, window_end=CONFIG.as_of)
    assert round(first.wip, 1) == 47.2
    assert round(second.wip, 1) == 68.2
    year = execution_flow(initiatives, window_start=CONFIG.start_ts, window_end=CONFIG.as_of)
    assert round(year.lead_time_days) == 149
    assert round(year.implied_lead_time) == 197
    assert round(year.lead_time_at_wip(year.wip / 2)) == 98


# 9 and 10 -------------------------------------------------------------------------------------


def test_finding_9_scores() -> None:
    ideas = generate_ideas(SynthConfig(seed=2026)).ideas
    assert len(ideas) == 628 and int(ideas["solution_fit"].sum()) == 109
    table = score_validity(ideas)
    assert table.loc["rice", "precision_top20"] == pytest.approx(0.262, abs=5e-4)
    assert table.loc["ice", "precision_top20"] == pytest.approx(0.238, abs=5e-4)
    assert table.loc["rice", "base_rate"] == pytest.approx(0.174, abs=5e-4)
    assert table.loc["rice", "spearman_with_value"] == pytest.approx(0.200, abs=5e-4)
    assert table.loc["ice", "spearman_with_value"] == pytest.approx(0.155, abs=5e-4)
    assert float(prob_above(2, 5, 0.35)) == pytest.approx(0.58, abs=5e-3)


def test_finding_9_triage_kills(policies: pd.DataFrame) -> None:
    kills = policies.xs("triage_kills_of_good", level="metric")["mean"]
    assert kills["Evidência"] == 25
    assert kills["Rigor máximo"] == 64


def test_finding_10_policy_table(policies: pd.DataFrame) -> None:
    mean = policies["mean"].unstack("metric")
    expected = {
        "Sem gates": (628.0, 109.0, 519.0, -124.6),
        "Intuição": (85.8, 50.4, 4.7, 19.8),
        "Evidência": (77.5, 58.5, 0.2, 24.3),
        "Rigor máximo": (41.1, 31.7, 0.0, 16.6),
        "Calibrada": (110.4, 87.1, 2.5, 31.5),
    }
    for policy, (mvps, good, bad, net) in expected.items():
        row = mean.loc[policy]
        assert round(row["mvps_built"], 1) == mvps
        assert round(row["good_scaled"], 1) == good
        assert round(row["bad_scaled"], 1) == bad
        assert round(row["net_value"] / 1e6, 1) == net

    net = policies.xs("net_value", level="metric")[["low", "high"]] / 1e6
    assert net.round(1).loc["Intuição"].tolist() == [13.3, 25.6]
    assert net.round(1).loc["Evidência"].tolist() == [16.7, 31.2]
    assert net.round(1).loc["Rigor máximo"].tolist() == [10.9, 19.6]
    assert net.round(1).loc["Calibrada"].tolist() == [26.9, 35.8]
    # The calibrated policy's worst run is above intuition's best.
    assert net.loc["Calibrada", "low"] > net.loc["Intuição", "high"]


def test_finding_10_uniform_prior_defect() -> None:
    assert float(prob_above(0, 2, 0.04, prior=(1.0, 1.0))) == pytest.approx(0.88, abs=5e-3)


# Examples -------------------------------------------------------------------------------------


@pytest.mark.parametrize("script", sorted((ROOT / "examples").glob("*.py")), ids=lambda p: p.name)
def test_every_example_runs(script: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", [str(script)])
    runpy.run_path(str(script), run_name="__main__")
