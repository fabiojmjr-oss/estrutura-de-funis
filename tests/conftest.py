"""Shared fixtures.

The hand-built event log below is small enough that every expected value in the tests that use it
was derived on paper. A metric tested only against its own implementation tests nothing.
"""

from __future__ import annotations

import pandas as pd
import pytest

from funilab.core import Funnel

ABC = Funnel("abc", ("A", "B", "C"))


@pytest.fixture
def funnel() -> Funnel:
    return ABC


@pytest.fixture
def events() -> pd.DataFrame:
    """Five entities through A -> B -> C.

    ======  ==========  ==========  ==========  ============================================
    Entity  A           B           C           Case
    ======  ==========  ==========  ==========  ============================================
    e1      Jan 1       Jan 3       Jan 10      converts, 9 days end to end
    e2      Jan 1       Jan 5       -           stops at B
    e3      Jan 2       -           -           stops at A
    e4      -           Jan 4       Jan 30      enters at B (skipped A), converts late
    e5      Feb 20      Feb 21      -           entered late: immature at an early as_of
    ======  ==========  ==========  ==========  ============================================
    """
    rows = [
        ("e1", "A", "2025-01-01"),
        ("e1", "B", "2025-01-03"),
        ("e1", "C", "2025-01-10"),
        ("e2", "A", "2025-01-01"),
        ("e2", "B", "2025-01-05"),
        ("e3", "A", "2025-01-02"),
        ("e4", "B", "2025-01-04"),
        ("e4", "C", "2025-01-30"),
        ("e5", "A", "2025-02-20"),
        ("e5", "B", "2025-02-21"),
    ]
    frame = pd.DataFrame(rows, columns=["entity_id", "stage", "ts"])
    frame["ts"] = pd.to_datetime(frame["ts"])
    return frame
