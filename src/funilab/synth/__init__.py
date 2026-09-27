"""Seeded synthetic data for every funnel in the package.

Each funnel draws from its own random stream, so the same seed yields the same numbers on any
machine and adding a funnel never moves another's figures. No record originates from a real
business; see ``DISCLAIMER.md``.
"""

from .config import SynthConfig, arrival_times
from .ideation import DEFAULT_SOURCES, IdeationData, SourceProfile, generate_ideas
from .management import ManagementData, generate_management
from .marketing import DEFAULT_CHANNELS, ChannelProfile, MarketingData, generate_marketing
from .sales import SalesData, generate_sales
from .supply import SupplyData, generate_supply

__all__ = [
    "DEFAULT_CHANNELS",
    "DEFAULT_SOURCES",
    "ChannelProfile",
    "IdeationData",
    "ManagementData",
    "MarketingData",
    "SalesData",
    "SourceProfile",
    "SupplyData",
    "SynthConfig",
    "arrival_times",
    "generate_ideas",
    "generate_management",
    "generate_marketing",
    "generate_sales",
    "generate_supply",
]
