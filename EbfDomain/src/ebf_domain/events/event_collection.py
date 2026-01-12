"""
Event collection for storing and filtering domain events.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, TypeVar

from .domain_event import DomainEvent

TEvent = TypeVar('TEvent', bound=DomainEvent)


@dataclass
class EventCollection:
    """
    Collection of domain events with filtering and iteration support.

    EventCollection provides a type-safe way to store and query events.
    All filter methods return EventCollection to enable chaining.

    Usage:
        ```python
        events = EventCollection()
        events.add(TradeFilled(...))
        events.add(TradeAssigned(...))

        # Filter by type (returns EventCollection)
        fills = events.of_type(TradeFilled)

        # Chain filters
        recent_fills = (events
            .of_type(TradeFilled)
            .after(yesterday)
            .for_aggregate("TRADE-123"))

        # Convert to list when needed
        fill_list: list[TradeFilled] = recent_fills.to_list()
        ```
    """

    _events: list[DomainEvent] = field(default_factory=list)

    def add(self, event: DomainEvent) -> None:
        """
        Add an event to the collection.

        Args:
            event: Domain event to add
        """
        self._events.append(event)

    def add_all(self, events: list[DomainEvent]) -> None:
        """
        Add multiple events at once.

        Args:
            events: List of events to add
        """
        self._events.extend(events)

    def of_type(self, event_type: type[TEvent]) -> 'EventCollection':
        """
        Get all events of a specific type.

        Returns EventCollection to allow chaining.

        Args:
            event_type: Event class to filter by

        Returns:
            New EventCollection containing only events of the specified type

        Example:
            ```python
            fills = events.of_type(TradeFilled)
            for fill in fills:
                print(f"Filled {fill.quantity} @ {fill.fill_price}")
            ```
        """
        filtered = [e for e in self._events if isinstance(e, event_type)]
        return EventCollection(filtered)

    def after(self, timestamp: datetime) -> 'EventCollection':
        """
        Get all events that occurred after a timestamp.

        Args:
            timestamp: Cutoff timestamp (exclusive)

        Returns:
            New EventCollection with filtered events
        """
        filtered = [e for e in self._events if e.occurred_at > timestamp]
        return EventCollection(filtered)

    def before(self, timestamp: datetime) -> 'EventCollection':
        """
        Get all events that occurred before a timestamp.

        Args:
            timestamp: Cutoff timestamp (exclusive)

        Returns:
            New EventCollection with filtered events
        """
        filtered = [e for e in self._events if e.occurred_at < timestamp]
        return EventCollection(filtered)

    def for_aggregate(self, aggregate_id) -> 'EventCollection':
        """
        Get all events for a specific aggregate.

        Args:
            aggregate_id: ID of the aggregate to filter by

        Returns:
            New EventCollection with filtered events
        """
        filtered = [e for e in self._events if e.aggregate_id == aggregate_id]
        return EventCollection(filtered)

    def where(self, predicate: Callable[[DomainEvent], bool]) -> 'EventCollection':
        """
        Filter events using a custom predicate.

        Args:
            predicate: Function that returns True for events to include

        Returns:
            New EventCollection with filtered events

        Example:
            ```python
            high_value = events.where(
                lambda e: isinstance(e, TradeFilled) and e.fill_price.amount > 100
            )
            ```
        """
        filtered = [e for e in self._events if predicate(e)]
        return EventCollection(filtered)

    @property
    def count(self) -> int:
        """Get the number of events in this collection."""
        return len(self._events)

    @property
    def is_empty(self) -> bool:
        """Check if the collection has no events."""
        return len(self._events) == 0

    @property
    def has_events(self) -> bool:
        """Check if the collection has any events."""
        return len(self._events) > 0

    def first(self) -> DomainEvent | None:
        """
        Get the first event, or None if empty.

        Returns:
            First event or None
        """
        return self._events[0] if self._events else None

    def last(self) -> DomainEvent | None:
        """
        Get the last event, or None if empty.

        Returns:
            Last event or None
        """
        return self._events[-1] if self._events else None

    def to_list(self) -> list[DomainEvent]:
        """
        Get all events as a list (defensive copy).

        Returns:
            New list containing all events
        """
        return list(self._events)

    def clear(self) -> None:
        """Remove all events from the collection."""
        self._events.clear()

    def __iter__(self):
        """Allow iteration over events."""
        return iter(self._events)

    def __len__(self) -> int:
        """Get the number of events."""
        return len(self._events)

    def __bool__(self) -> bool:
        """Collection is truthy if it has events."""
        return bool(self._events)
