"""The marketing funnel: Lead, MQL, SQL, customer.

:func:`cac_table` shows how much of a CAC is the choice of denominator, and
:func:`attribution_table` how much of a channel ranking is the choice of attribution model. The
conversion itself is measured with :mod:`funilab.core` on the ``MARKETING`` funnel.
"""

from .acquisition import (
    MODELS,
    attribution,
    attribution_table,
    cac_by_attribution,
    cac_table,
    payback_months,
)
from .stages import MARKETING

__all__ = [
    "MARKETING",
    "MODELS",
    "attribution",
    "attribution_table",
    "cac_by_attribution",
    "cac_table",
    "payback_months",
]
