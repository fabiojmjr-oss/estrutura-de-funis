"""Export the figures and portfolios the web interface reads.

Run:
    python -m funilab.export web/data

The web interface (``web/``) is a static page with its own JavaScript engine, so it works offline,
on a phone, and from a shared link without a server running Python. That independence has a cost:
two implementations of the same arithmetic can drift. This module is the bridge that prevents it.

It writes two kinds of file. **Data** files (one per funnel) carry what the page displays and the
inputs its engine recomputes from. The **parity** file carries test vectors - inputs and the
answers Python gives - which the JavaScript test suite asserts against, so a formula changed on
one side and not the other fails a build instead of showing a different number to a user.

Every float is rounded to a fixed number of places, so a regeneration that changes nothing
produces byte-identical files, and a stale committed file is detectable by a test.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .core import conversion_sensitivity, funnel_table, wilson_interval
from .ideation import (
    BASELINE_POLICIES,
    IDEA_TO_SOLUTION,
    CycleCosts,
    compare_policies,
    decide,
    neutral_prior,
    prob_above,
    sample_size,
)
from .ideation.evidence import beta_cdf
from .management import EXECUTION, benefit_bridge, execution_flow
from .marketing import MARKETING, MODELS, attribution, cac_table
from .sales import CRM_DEFAULT_PROBABILITY, PIPELINE, stage_age, stage_probabilities
from .sales import stale_threshold as sales_stale_threshold
from .supply import FULFILMENT, hidden_factory, perfect_order, yield_table
from .synth import (
    SynthConfig,
    generate_ideas,
    generate_management,
    generate_marketing,
    generate_sales,
    generate_supply,
)

PLACES = 6
HOLDOUT = SynthConfig(seed=2026)
WINDOW = pd.Timedelta(days=120)


def _clean(value: Any) -> Any:
    """Make a value JSON-safe and stable: rounded floats, None for NaN, plain Python types."""
    if isinstance(value, dict):
        return {str(k): _clean(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_clean(v) for v in value]
    if isinstance(value, np.bool_ | bool):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, float | np.floating):
        if not np.isfinite(value):
            return None
        rounded = round(float(value), PLACES)
        return int(rounded) if rounded.is_integer() and abs(rounded) < 2**53 else rounded
    return value


def _stage_rows(table: pd.DataFrame) -> list[dict[str, Any]]:
    return [{"stage": stage, "entered": int(row["entered"])} for stage, row in table.iterrows()]


def marketing_payload(config: SynthConfig) -> dict[str, Any]:
    data = generate_marketing(config)
    start, end = config.start_ts, config.as_of
    customers = data.leads.loc[data.leads["Cliente"].between(start, end), "lead_id"]
    journeys = (
        data.touches.loc[data.touches["lead_id"].isin(customers)]
        .sort_values(["lead_id", "touch"])
        .groupby("lead_id")["channel"]
        .agg(tuple)
        .value_counts()
    )
    spend = (
        data.spend.loc[data.spend["month"].between(start, end)].groupby("channel")["spend"].sum()
    )
    cac = cac_table(data.leads, data.spend, start=start, end=end)
    by_source = cac.drop(index=["paid (total)", "blended (total)"])["customers"]
    quarters = {}
    for label, q_start, q_end in (
        ("Q3", "2025-07-01", "2025-09-30"),
        ("Q4", "2025-10-01", "2025-12-31"),
    ):
        table = conversion_sensitivity(
            data.events,
            MARKETING,
            start=pd.Timestamp(q_start),
            end=pd.Timestamp(q_end),
            window=WINDOW,
            as_of=config.as_of,
        )
        quarters[label] = table.reset_index().to_dict(orient="records")
    matured = funnel_table(
        data.events, MARKETING, window=WINDOW, as_of=config.as_of, mature_only=True
    )
    return {
        "stages": list(MARKETING.stages),
        "funnel": _stage_rows(matured),
        "conventions": quarters,
        "spend": spend.to_dict(),
        "customers_by_source": by_source.to_dict(),
        "journeys": [
            {"path": list(path), "customers": int(count)}  # type: ignore[call-overload]
            for path, count in journeys.items()
        ],
    }


def sales_payload(config: SynthConfig) -> dict[str, Any]:
    data = generate_sales(config)
    deals = data.opportunities
    open_deals = deals.loc[deals["status"] == "open"].copy()
    open_deals["days_in_stage"] = stage_age(deals, config.as_of)
    return {
        "stages": list(PIPELINE.stages),
        "funnel_infer": _stage_rows(funnel_table(data.events, PIPELINE)),
        "funnel_literal": _stage_rows(funnel_table(data.events, PIPELINE, skipped="literal")),
        "crm_probability": CRM_DEFAULT_PROBABILITY,
        "historical_probability": stage_probabilities(data.events, deals, PIPELINE).to_dict(),
        "stale_after_days": sales_stale_threshold(data.events, deals, PIPELINE).to_dict(),
        "open_deals": [
            {
                "stage": row.current_stage,
                "amount": row.amount,
                "days_in_stage": row.days_in_stage,
                "won": row.eventual_status == "won",
            }
            for row in open_deals.itertuples()
        ],
    }


def supply_payload(config: SynthConfig) -> dict[str, Any]:
    data = generate_supply(config)
    table = yield_table(data.attempts, FULFILMENT.stages[1:])
    perfect = perfect_order(data.orders)["rate"]
    return {
        "stages": list(FULFILMENT.stages),
        "funnel": _stage_rows(funnel_table(data.events, FULFILMENT)),
        "yields": table.reset_index().to_dict(orient="records"),
        "hidden_factory": hidden_factory(data.attempts, data.orders),
        "perfect_order": perfect.to_dict(),
    }


def management_payload(config: SynthConfig) -> dict[str, Any]:
    data = generate_management(config)
    initiatives = data.initiatives
    cohort = initiatives.loc[initiatives["proposed_ts"] < config.start_ts]
    bridge = benefit_bridge(cohort, EXECUTION)
    year = execution_flow(initiatives, window_start=config.start_ts, window_end=config.as_of)
    return {
        "stages": list(EXECUTION.stages),
        "funnel": _stage_rows(funnel_table(data.events, EXECUTION)),
        "bridge": [{"bar": bar, "benefit": row["benefit"]} for bar, row in bridge.iterrows()],
        "flow": {
            "wip": year.wip,
            "throughput_per_day": year.throughput_per_day,
            "lead_time_days": year.lead_time_days,
            "implied_lead_time": year.implied_lead_time,
        },
    }


def ideation_payload(*, replications: int = 30) -> dict[str, Any]:
    ideas = generate_ideas(HOLDOUT).ideas
    columns = [
        "source",
        "reach",
        "impact",
        "confidence",
        "effort",
        "ease",
        "solution_fit",
        "value_if_scaled",
        "true_pain_rate",
        "true_signup_rate",
        "true_retention",
    ]
    reference = compare_policies(
        ideas,
        replications=replications,
        metrics=("mvps_built", "good_scaled", "bad_scaled", "false_kills", "spend", "net_value"),
    )
    return {
        "stages": list(IDEA_TO_SOLUTION.stages),
        "seed": HOLDOUT.seed,
        "ideas": {column: ideas[column].tolist() for column in columns},
        "costs": vars(CycleCosts()),
        "policies": [vars(policy) for policy in BASELINE_POLICIES],
        "reference": [
            {"policy": policy, "metric": metric, **reference.loc[(policy, metric)].to_dict()}
            for policy, metric in reference.index
        ],
        "replications": replications,
    }


def parity_payload() -> dict[str, Any]:
    """Inputs and Python's answers, for the JavaScript suite to assert against."""
    beta = [(x, a, b) for x in (0.02, 0.3, 0.5, 0.87) for a, b in ((0.5, 2), (3, 7), (40, 60))]
    counts = [(0, 2), (2, 5), (4, 10), (8, 20), (18, 20), (42, 600)]
    bars = (0.04, 0.33, 0.35)
    journeys = [
        ["Social", "Busca"],
        ["Eventos", "Social", "Social", "Busca"],
        ["Busca"],
        ["Indicação", "Eventos", "Busca"],
    ]
    touches = pd.DataFrame(
        [
            (f"c{i}", t, channel)
            for i, path in enumerate(journeys)
            for t, channel in enumerate(path)
        ],
        columns=["lead_id", "touch", "channel"],
    )
    customers = [f"c{i}" for i in range(len(journeys))]
    low, high = wilson_interval(np.array([0, 5, 37]), np.array([10, 10, 250]))
    return {
        "beta_cdf": [
            {"x": x, "a": a, "b": b, "value": float(beta_cdf(x, a, b))} for x, a, b in beta
        ],
        "neutral_prior": [{"bar": bar, "prior": list(neutral_prior(bar))} for bar in bars],
        "prob_above": [
            {"k": k, "n": n, "bar": bar, "value": float(prob_above(k, n, bar))}
            for k, n in counts
            for bar in bars
        ],
        "decide": [
            {
                "k": k,
                "n": n,
                "bar": 0.35,
                "go": 0.6,
                "kill": 0.2,
                "value": str(decide(k, n, 0.35, go=0.6, kill=0.2)),
            }
            for k, n in counts
        ],
        "sample_size": [
            {"rate": rate, "bar": bar, "go": go, "value": sample_size(rate, bar, go=go)}
            for rate, bar, go in (
                (0.07, 0.04, 0.8),
                (0.02, 0.04, 0.8),
                (0.045, 0.04, 0.8),
                (0.45, 0.33, 0.8),
                (0.07, 0.04, 0.6),
            )
        ],
        "wilson": [
            {"k": k, "n": n, "low": float(lo), "high": float(hi)}
            for k, n, lo, hi in zip((0, 5, 37), (10, 10, 250), low, high, strict=True)
        ],
        "attribution": {
            "journeys": journeys,
            "credits": {
                model: attribution(touches, customers, model).to_dict() for model in MODELS
            },
        },
    }


def build_payloads(*, replications: int = 30) -> dict[str, dict[str, Any]]:
    """Every file the web interface reads, keyed by file name."""
    config = SynthConfig()
    payloads = {
        "marketing.json": marketing_payload(config),
        "sales.json": sales_payload(config),
        "supply.json": supply_payload(config),
        "management.json": management_payload(config),
        "ideation.json": ideation_payload(replications=replications),
        "parity.json": parity_payload(),
    }
    return {name: _clean(payload) for name, payload in payloads.items()}


def serialise(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n"


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    out = Path(args[0] if args else "web/data")
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in build_payloads().items():
        (out / name).write_text(serialise(payload), encoding="utf-8")
        print(f"wrote {out / name}")


if __name__ == "__main__":
    main()
