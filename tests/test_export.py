"""The bridge to the web interface: stable serialisation, and committed data that is not stale.

The page reads ``web/data/*.json`` and its JavaScript suite asserts parity against
``web/data/parity.json``. Both are only as good as the files being current, so the slow test
regenerates every file and compares it byte for byte with what is committed.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from funilab.export import _clean, build_payloads, parity_payload, serialise

ROOT = Path(__file__).resolve().parents[1]


def test_clean_makes_values_stable_and_json_safe() -> None:
    cleaned = _clean(
        {"a": np.float64(1 / 3), "b": math.nan, "c": np.int64(4), "d": (np.bool_(True), 2.0)}
    )
    assert cleaned == {"a": 0.333333, "b": None, "c": 4, "d": [True, 2]}


def test_serialisation_is_deterministic() -> None:
    payload = {"z": 1, "a": [1.5, "ç"]}
    assert serialise(payload) == serialise(dict(reversed(list(payload.items()))))
    assert serialise(payload).endswith("\n")
    assert "ç" in serialise(payload)


def test_parity_vectors_cover_every_engine_function() -> None:
    parity = parity_payload()
    assert set(parity) == {
        "beta_cdf",
        "neutral_prior",
        "prob_above",
        "decide",
        "sample_size",
        "wilson",
        "attribution",
    }
    assert {row["value"] for row in parity["decide"]} == {"go", "kill", "more evidence"}


@pytest.mark.slow
def test_committed_web_data_is_current() -> None:
    stale = []
    for name, payload in build_payloads().items():
        path = ROOT / "web" / "data" / name
        if not path.exists() or path.read_text(encoding="utf-8") != serialise(payload):
            stale.append(name)
    assert not stale, f"regenerate with `make web-data`: {stale}"
