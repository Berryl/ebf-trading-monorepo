# domain_event.py

"""
Domain event base classes for EbfDomain.

Events are immutable records of things that happened in the domain.
They use past-tense naming and capture the full context of what occurred.
"""

from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import ebf_core.guards.guards as g


@dataclass(frozen=True, kw_only=True)
class DomainEvent[TAggregateId](ABC):
    """
    Base class for all domain events.

    Events are immutable records of things that happened in the domain.
    They use past-tense naming and capture the full context of what occurred.

    Type Parameters:
        TAggregateId: The type of the aggregate's ID (str, int, UUID, TradeId, etc.)

    Attributes:
        event_id: Unique identifier for this event (always UUID)
        occurred_at: When the event occurred (business time, UTC timezone-aware)
        recorded_at: When the event was recorded in the system (system time, UTC timezone-aware)
        aggregate_id: ID of the aggregate that raised this event (type-safe)
        aggregate_type: Type name of the aggregate (for routing/filtering)
    """

    event_id: UUID
    occurred_at: datetime
    recorded_at: datetime
    aggregate_id: TAggregateId
    aggregate_type: str

    def __post_init__(self) -> None:
        g.ensure_not_none(self.event_id, "event_id")

        ensure_tz_aware(self.occurred_at, "occurred_at")
        ensure_tz_aware(self.recorded_at, "recorded_at")

        g.ensure_not_none(self.aggregate_id, "aggregate_id")
        g.ensure_str_is_valued(self.aggregate_type, "aggregate_type")

    @property
    def event_type(self) -> str:
        return self.__class__.__name__


def ensure_tz_aware(dt: datetime | None, field_name: str) -> datetime:
    g.ensure_not_none(dt, field_name)
    if dt.tzinfo is None:
        raise ValueError(
            f"{field_name!r} must be timezone-aware (use tzinfo=UTC or similar)"  # noqa
        )
    return dt
