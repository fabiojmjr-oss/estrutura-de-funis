from __future__ import annotations

import pandas as pd
import pytest

from funilab.core import Funnel
from funilab.management import benefit_bridge, execution_flow

F = Funnel("m", ("Proposta", "Aprovada", "Entregue", "Medido"))


@pytest.fixture
def initiatives() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "planned_benefit": [100.0, 200.0, 300.0, 400.0],
            "realised_benefit": [None, None, None, 250.0],
            "status": ["stopped", "stopped", "in_flight", "measured"],
            "stopped_at": ["Aprovada", "Medido", "", ""],
        }
    )


def test_benefit_bridge_reconciles_by_hand(initiatives: pd.DataFrame) -> None:
    bridge = benefit_bridge(initiatives, F)["benefit"]
    assert bridge["announced"] == 1000.0
    assert bridge["stopped before Aprovada"] == -100.0
    assert bridge["stopped before Medido"] == -200.0
    assert bridge["still in flight"] == -300.0
    assert bridge["under-delivered"] == -150.0
    assert bridge["realised"] == 250.0
    assert bridge.iloc[:-1].sum() == pytest.approx(bridge["realised"])


def test_execution_flow_uses_stop_date_for_stopped_projects() -> None:
    frame = pd.DataFrame(
        {
            "started_ts": pd.to_datetime(["2025-01-01", "2025-01-01"]),
            "delivered_ts": pd.to_datetime(["2025-01-11", None]),
            "stopped_ts": pd.to_datetime([None, "2025-01-06"]),
            "stopped_at": ["", "Entregue"],
        }
    )
    flow = execution_flow(
        frame, window_start=pd.Timestamp("2024-12-31"), window_end=pd.Timestamp("2025-01-31")
    )
    assert flow.completed == 2
    assert flow.lead_time_days == pytest.approx(7.5)
