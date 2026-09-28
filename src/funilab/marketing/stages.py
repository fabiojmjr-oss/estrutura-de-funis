"""The marketing funnel's stage order."""

from __future__ import annotations

from ..core import Funnel

MARKETING = Funnel("marketing", ("Lead", "MQL", "SQL", "Cliente"))
