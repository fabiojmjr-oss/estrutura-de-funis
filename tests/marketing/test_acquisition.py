from __future__ import annotations

import pandas as pd
import pytest

from funilab.marketing import (
    MODELS,
    attribution,
    attribution_table,
    cac_by_attribution,
    cac_table,
    payback_months,
)


@pytest.fixture
def touches() -> pd.DataFrame:
    """Three customer journeys and one non-customer.

    c1: Social -> Busca           (two touches)
    c2: Eventos -> Social -> Social -> Busca
    c3: Busca                     (one touch)
    n1: Social                    (did not convert, must be ignored)
    """
    rows = [
        ("c1", 0, "Social"),
        ("c1", 1, "Busca"),
        ("c2", 0, "Eventos"),
        ("c2", 1, "Social"),
        ("c2", 2, "Social"),
        ("c2", 3, "Busca"),
        ("c3", 0, "Busca"),
        ("n1", 0, "Social"),
    ]
    return pd.DataFrame(rows, columns=["lead_id", "touch", "channel"])


CUSTOMERS = ["c1", "c2", "c3"]


def test_first_and_last_touch(touches: pd.DataFrame) -> None:
    first = attribution(touches, CUSTOMERS, "first")
    last = attribution(touches, CUSTOMERS, "last")
    assert first.to_dict() == {"Busca": 1.0, "Eventos": 1.0, "Social": 1.0}
    # Every channel in a converting journey is listed, at zero if it closed none.
    assert last.to_dict() == {"Busca": 3.0, "Eventos": 0.0, "Social": 0.0}


def test_linear_and_position_by_hand(touches: pd.DataFrame) -> None:
    linear = attribution(touches, CUSTOMERS, "linear")
    assert linear["Busca"] == pytest.approx(0.5 + 0.25 + 1.0)
    assert linear["Social"] == pytest.approx(0.5 + 0.5)
    position = attribution(touches, CUSTOMERS, "position")
    # c1 splits 50/50; c2 is 40/10/10/40; c3 is all Busca.
    assert position["Busca"] == pytest.approx(0.5 + 0.4 + 1.0)
    assert position["Social"] == pytest.approx(0.5 + 0.2)
    assert position["Eventos"] == pytest.approx(0.4)


@pytest.mark.parametrize("model", MODELS)
def test_every_model_credits_exactly_one_customer_each(touches: pd.DataFrame, model: str) -> None:
    assert attribution(touches, CUSTOMERS, model).sum() == pytest.approx(3.0)  # type: ignore[arg-type]


def test_unknown_model_raises(touches: pd.DataFrame) -> None:
    with pytest.raises(ValueError):
        attribution(touches, CUSTOMERS, "time_decay")  # type: ignore[arg-type]


def test_attribution_table_ranks(touches: pd.DataFrame) -> None:
    table = attribution_table(touches, CUSTOMERS)
    assert table.loc["Busca", "rank_last"] == 1
    assert table.loc["Eventos", "last"] == 0.0


def test_cac_by_attribution(touches: pd.DataFrame) -> None:
    spend = pd.Series({"Busca": 300.0, "Social": 100.0, "Eventos": 50.0, "Organico": 0.0})
    table = cac_by_attribution(touches, CUSTOMERS, spend)
    assert "Organico" not in table.index
    assert table.loc["Busca", "cac_first"] == pytest.approx(300.0)
    assert table.loc["Busca", "cac_last"] == pytest.approx(100.0)


def test_cac_table_blended_versus_paid() -> None:
    leads = pd.DataFrame(
        {
            "lead_id": ["a", "b", "c", "d"],
            "channel": ["Pago", "Pago", "Indicação", "Pago"],
            "Cliente": pd.to_datetime(["2025-01-10", "2025-01-20", "2025-01-15", None]),
        }
    )
    spend = pd.DataFrame(
        {"month": pd.to_datetime(["2025-01-01"]), "channel": ["Pago"], "spend": [1000.0]}
    )
    table = cac_table(
        leads, spend, start=pd.Timestamp("2025-01-01"), end=pd.Timestamp("2025-01-31")
    )
    assert table.loc["paid (total)", "cac"] == pytest.approx(500.0)
    assert table.loc["blended (total)", "cac"] == pytest.approx(1000.0 / 3)


def test_payback() -> None:
    assert payback_months(1200, 100) == pytest.approx(12.0)
    assert payback_months(1200, 0) == float("inf")
