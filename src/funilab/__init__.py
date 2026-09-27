"""Funnel analytics toolkit.

One engine and five funnels, in dependency order:

``funilab.synth``
    Seeded synthetic event logs for every funnel. Every example is built on it, so results are
    reproducible and no real business is exposed.
``funilab.core``
    The funnel engine: stage definitions, conversion under explicit conventions, confidence
    intervals, stage durations, levers and Little's law.
``funilab.marketing``, ``funilab.sales``, ``funilab.supply``, ``funilab.management``
    One module per business funnel, each answering the question that funnel is usually read for.
``funilab.ideation``
    The idea-to-MVP cycle: scoring, evidence at each gate, and the economics of a gate policy.
"""

__version__ = "0.1.0"

__all__ = ["__version__"]
