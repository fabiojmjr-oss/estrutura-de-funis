"""The strategy execution funnel: proposal to measured benefit.

:func:`benefit_bridge` reconciles announced benefit to realised benefit gate by gate, and
:func:`execution_flow` measures the portfolio's work in progress, throughput and lead time.
"""

from .portfolio import benefit_bridge, execution_flow
from .stages import EXECUTION

__all__ = ["EXECUTION", "benefit_bridge", "execution_flow"]
