"""The sales pipeline's stage order and the probabilities a CRM ships with."""

from __future__ import annotations

from ..core import Funnel

PIPELINE = Funnel("sales", ("Prospecção", "Qualificação", "Proposta", "Negociação", "Ganho"))

# The stage probabilities a CRM is configured with on day one and rarely revisited. They are
# round numbers chosen by whoever installed it, not estimates from this pipeline's history.
CRM_DEFAULT_PROBABILITY: dict[str, float] = {
    "Prospecção": 0.10,
    "Qualificação": 0.25,
    "Proposta": 0.50,
    "Negociação": 0.75,
}
