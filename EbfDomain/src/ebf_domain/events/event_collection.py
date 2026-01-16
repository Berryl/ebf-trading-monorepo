# event_collection.py

"""
Event collection for storing and filtering domain events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, TypeVar, Self

from ebf_domain.events.domain_event import DomainEvent

TEvent = TypeVar("TEvent", bound=DomainEvent)


@dataclass
class EventCollection:
    """
    Collection of domain events with filtering and iteration support.
    """

    _events: list[DomainEvent[object]] = field(default_factory=list)

    def add(self, event: DomainEvent) -> Self:
        self._events.append(event)
        return self

    def add_all(self, events: list[DomainEvent]) -> None:
        self._events.extend(events)

    def of_type(self, event_type: type[TEvent]) -> "EventCollection":
        filtered = [e for e in self._events if isinstance(e, event_type)]
        return EventCollection(filtered)

    def after(self, timestamp: datetime) -> "EventCollection":
        filtered = [e for e in self._events if e.occurred_at > timestamp]
        return EventCollection(filtered)

    def before(self, timestamp: datetime) -> "EventCollection":
        filtered = [e for e in self._events if e.occurred_at < timestamp]
        return EventCollection(filtered)

    def for_aggregate(self, aggregate_id) -> "EventCollection":
        filtered = [e for e in self._events if e.aggregate_id == aggregate_id]
        return EventCollection(filtered)

    def where(self, predicate: Callable[[DomainEvent], bool]) -> "EventCollection":
        filtered = [e for e in self._events if predicate(e)]
        return EventCollection(filtered)

    @property
    def count(self) -> int:
        return len(self._events)

    @property
    def is_empty(self) -> bool:
        return len(self._events) == 0

    @property
    def has_events(self) -> bool:
        return len(self._events) > 0

    def first(self) -> DomainEvent | None:
        return self._events[0] if self._events else None

    def last(self) -> DomainEvent | None:
        return self._events[-1] if self._events else None

    def to_list(self) -> list[DomainEvent]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()

    def __iter__(self):
        return iter(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def __bool__(self) -> bool:
        return bool(self._events)
