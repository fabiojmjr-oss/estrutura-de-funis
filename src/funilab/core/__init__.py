"""The funnel engine shared by every business funnel in the package.

Conversion under explicit conventions (:func:`funnel_table`, :func:`conversion_sensitivity`), the
uncertainty of a rate (:func:`wilson_interval`), where to push (:func:`lever_table`), how much to
feed it (:func:`required_top`) and how long it takes (:func:`stage_durations`,
:func:`littles_law`).
"""

from .conversion import (
    conversion_sensitivity,
    funnel_table,
    period_rates,
    reached,
    wilson_interval,
)
from .flow import LittleResult, littles_law, stage_durations
from .funnel import EVENT_COLUMNS, Funnel, FunnelDataError, validate_events
from .levers import expected_output, lever_table, required_top

__all__ = [
    "EVENT_COLUMNS",
    "Funnel",
    "FunnelDataError",
    "LittleResult",
    "conversion_sensitivity",
    "expected_output",
    "funnel_table",
    "lever_table",
    "littles_law",
    "period_rates",
    "reached",
    "required_top",
    "stage_durations",
    "validate_events",
    "wilson_interval",
]
