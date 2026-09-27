"""The strategy execution funnel's stage order."""

from __future__ import annotations

from ..core import Funnel

EXECUTION = Funnel(
    "management",
    ("Proposta", "Aprovada", "Financiada", "Em execução", "Entregue", "Benefício medido"),
)
