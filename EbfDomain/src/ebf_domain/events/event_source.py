"""
EventSource mixin for domain aggregates that raise events.
"""

from dataclasses import dataclass, field, KW_ONLY
from datetime import UTC, datetime
from uuid import uuid4, UUID

from ebf_domain.events.domain_event import DomainEvent
from ebf_domain.events.event_collection import EventCollection


@dataclass
class EventSource:
    """
    Mixin for domain aggregates that raise and collect events.

    EventSource owns event metadata (timestamps, aggregate identity/type).
    """

    _: KW_ONLY
    _pending_events: EventCollection = field(default_factory=EventCollection, init=False, repr=False)
    _tbd_event_aggregate_id: UUID = field(default_factory=uuid4, init=False, repr=False)

    @property
    def aggregate_type(self) -> str:
        return self.__class__.__name__

    @property
    def aggregate_id_for_events(self):
        # Works with IDBase[T] or any class exposing `id_value`.
        id_value = getattr(self, "id_value", None)
        return id_value if id_value is not None else self._tbd_event_aggregate_id

    def _event_metadata(self, occurred_at: datetime | None = None) -> dict:
        now = datetime.now(UTC)
        return {
            "event_id": uuid4(),
            "occurred_at": occurred_at or now,
            "recorded_at": now,
            "aggregate_id": self.aggregate_id_for_events,
            "aggregate_type": self.aggregate_type,
        }

    def record(self, event_type: type[DomainEvent], *, occurred_at: datetime | None = None, **payload) -> None:
        self.record_event(event_type(**self._event_metadata(occurred_at), **payload))

    def record_event(self, event: DomainEvent) -> None:
        self._pending_events.add(event)

    def peek_events(self) -> list[DomainEvent]:
        return self._pending_events.to_list()

    def collect_events(self) -> list[DomainEvent]:
        events = self._pending_events.to_list()
        self._pending_events.clear()
        return events

    @property
    def has_events(self) -> bool:
        return self._pending_events.has_events

    @property
    def event_count(self) -> int:
        return self._pending_events.count
