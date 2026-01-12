"""
EventSource mixin for domain aggregates that raise events.
"""

from dataclasses import dataclass, field, KW_ONLY

from .domain_event import DomainEvent
from .event_collection import EventCollection


@dataclass
class EventSource:
    """
    Mixin for domain aggregates that raise and collect events.

    EventSource manages a private collection of domain events that have
    occurred on the aggregate. Events can be peeked at or collected (cleared).

    This mixin is designed to work alongside IDBase[T] for aggregates that
    need both ID management and event tracking.

    Usage:
        ```python
        from dataclasses import dataclass
        from ebf_domain.id_base import IDBase
        from ebf_domain.events import EventSource, DomainEvent

        @dataclass(eq=False)
        class Trade[T](IDBase[T], EventSource):
            symbol: str
            quantity: int

            @staticmethod
            def open(symbol: str, quantity: int) -> 'Trade[str]':
                trade = Trade(symbol=symbol, quantity=quantity)
                trade.resolve_id("TRADE-001")
                trade.record_event(TradeOpened(...))
                return trade

            def fill(self, price: Money) -> None:
                # Business logic here
                self.record_event(TradeFilled(...))
        ```

    Integration with IDBase:
        When using EventSource with IDBase[T], be aware that:
        - You can record events on TBD aggregates (they queue up)
        - Event aggregate_id will use whatever ID the aggregate has
        - Best practice: resolve ID before recording events, or use
          a temporary ID during creation

    Design Notes:
        - Uses KW_ONLY to avoid dataclass field ordering conflicts
        - EventCollection is private (_pending_events)
        - Provides both peek (read-only) and collect (destructive) access
    """

    _: KW_ONLY
    _pending_events: EventCollection = field(default_factory=EventCollection, init=False, repr=False)

    def record_event(self, event: DomainEvent) -> None:
        """
        Record a domain event that occurred on this aggregate.

        Events are stored in an internal collection until collected.

        Args:
            event: Domain event to record

        Example:
            ```python
            trade.record_event(TradeFilled(
                **DomainEvent.make_metadata(trade.id, "Trade"),
                trade_id=trade.id,
                fill_price=Money.mint(100, USD),
                quantity=10
            ))
            ```
        """
        self._pending_events.add(event)

    def peek_events(self) -> list[DomainEvent]:
        """
        View pending events without removing them.

        Useful for testing and inspecting state without side effects.

        Returns:
            List of pending events (defensive copy)
        """
        return self._pending_events.to_list()

    def collect_events(self) -> list[DomainEvent]:
        """
        Collect and clear all pending events.

        This is typically called by the repository after saving the aggregate,
        or by an event dispatcher to publish events.

        Returns:
            List of all pending events (events are removed from aggregate)

        Example:
            ```python
            # Service or repository collects events for publishing
            events = trade.collect_events()
            for event in events:
                event_bus.publish(event)
            ```
        """
        events = self._pending_events.to_list()
        self._pending_events.clear()
        return events

    @property
    def has_events(self) -> bool:
        """Check if there are any pending events."""
        return self._pending_events.has_events

    @property
    def event_count(self) -> int:
        """Get the number of pending events."""
        return self._pending_events.count
