"""Funnel definition and event-log validation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

EVENT_COLUMNS: tuple[str, ...] = ("entity_id", "stage", "ts")


class FunnelDataError(ValueError):
    """Raised when an event log breaks the contract. Lists every problem found, not the first."""


@dataclass(frozen=True)
class Funnel:
    """An ordered sequence of stages that an entity can reach.

    A funnel is only a claim about order. Whether an entity that appears at a later stage without
    a record at an earlier one *passed through* it is a convention, and it is decided per call by
    the ``skipped`` argument of the conversion functions rather than here.
    """

    name: str
    stages: tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.stages) < 2:
            raise ValueError("a funnel needs at least two stages")
        if len(set(self.stages)) != len(self.stages):
            raise ValueError(f"duplicate stages in funnel {self.name!r}: {self.stages}")

    @property
    def top(self) -> str:
        return self.stages[0]

    @property
    def bottom(self) -> str:
        return self.stages[-1]

    @property
    def transitions(self) -> list[tuple[str, str]]:
        return list(zip(self.stages[:-1], self.stages[1:], strict=True))

    def index(self, stage: str) -> int:
        return self.stages.index(stage)


def validate_events(events: pd.DataFrame, funnel: Funnel) -> None:
    """Check an event log against the contract and report every problem in one pass.

    The contract is one row per entity and stage reached, with the timestamp it was reached:
    ``entity_id``, ``stage``, ``ts``. Extra columns are allowed and ignored.
    """
    problems: list[str] = []
    missing = [column for column in EVENT_COLUMNS if column not in events.columns]
    if missing:
        raise FunnelDataError(f"missing columns: {missing}")

    unknown = sorted(set(events["stage"].dropna().unique()) - set(funnel.stages))
    if unknown:
        problems.append(f"stages not in funnel {funnel.name!r}: {unknown}")
    if not pd.api.types.is_datetime64_any_dtype(events["ts"]):
        problems.append("column 'ts' is not a datetime")
    if events["entity_id"].isna().any():
        problems.append(f"{int(events['entity_id'].isna().sum())} rows without entity_id")
    if events["ts"].isna().any():
        problems.append(f"{int(events['ts'].isna().sum())} rows without a timestamp")
    if problems:
        raise FunnelDataError("; ".join(problems))
