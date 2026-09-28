"""The sales pipeline: prospecting to won.

:func:`win_rates` returns the four win rates one pipeline supports, :func:`stage_probabilities`
replaces the CRM's round numbers with the pipeline's own history, and
:func:`weighted_forecast` prices the difference. :func:`stale_threshold` marks the deals whose
age in stage is itself the evidence against them.
"""

from .pipeline import (
    forecast_table,
    sales_velocity,
    stage_age,
    stage_probabilities,
    stale_threshold,
    weighted_forecast,
    win_rates,
)
from .stages import CRM_DEFAULT_PROBABILITY, PIPELINE

__all__ = [
    "CRM_DEFAULT_PROBABILITY",
    "PIPELINE",
    "forecast_table",
    "sales_velocity",
    "stage_age",
    "stage_probabilities",
    "stale_threshold",
    "weighted_forecast",
    "win_rates",
]
