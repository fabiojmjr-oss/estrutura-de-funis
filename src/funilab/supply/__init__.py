"""The order fulfilment funnel: order, credit, picking, checking, dispatch, delivery.

:func:`yield_table` sets rolled throughput yield beside the final yield, :func:`hidden_factory`
counts the repeat work between them, and :func:`perfect_order` shows what multiplying component
rates assumes about how they fail.
"""

from .stages import FULFILMENT
from .yields import PERFECT_ORDER_COMPONENTS, hidden_factory, perfect_order, yield_table

__all__ = [
    "FULFILMENT",
    "PERFECT_ORDER_COMPONENTS",
    "hidden_factory",
    "perfect_order",
    "yield_table",
]
