"""The order fulfilment funnel's stage order."""

from __future__ import annotations

from ..core import Funnel

FULFILMENT = Funnel(
    "supply", ("Pedido", "Crédito", "Separação", "Conferência", "Expedição", "Entrega")
)
