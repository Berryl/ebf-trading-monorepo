"""
Domain event base classes for EbfDomain.

Events are immutable records of things that happened in the domain.
They use past-tense naming and capture the full context of what occurred.
"""

from abc import ABC
from dataclasses import dataclass
from datetime import UTC, datetime
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

    Temporal Semantics:
        Following Fowler's TemporalObject pattern, events track both:
        - occurred_at: Business time (when the real-world event happened)
        - recorded_at: System time (when the system learned about it)

        This distinction supports several use cases:
        - Historical data migration (occurred 6 months ago, recorded today)
        - Delayed notifications (filled at 2:30 PM, notified at 2:31 PM)
        - Audit trails (when did we know about this?)
        - Time-series analysis (query by occurrence vs. recording)

    Usage:
        # noinspection GrazieInspection
        ```python
        from dataclasses import dataclass
        from uuid import uuid4
        from datetime import datetime, UTC

        @dataclass(frozen=True, kw_only=True)
        class TradeFilled(DomainEvent[str]):
            trade_id: str
            leg_id: str
            fill_price: Money
            quantity: int
            commission: Money

        # Synchronous event (occurred_at = recorded_at)
        event = TradeFilled(
            **DomainEvent.make_metadata("TRADE-123", "Trade"),
            trade_id="TRADE-123",
            leg_id="LEG-456",
            fill_price=Money.mint(100.50, USD),
            quantity=10,
            commission=Money.mint(0.50, USD)
        )

        # Historical event (migration scenario)
        event = TradeFilled(
            **DomainEvent.make_metadata(
                "TRADE-123",
                "Trade",
                occurred_at=datetime(2024, 7, 15, 14, 30, UTC)  # 6 months ago
            ),
            # recorded_at automatically set to now (migration time)
            trade_id="TRADE-123",
            leg_id="LEG-456",
            fill_price=Money.mint(100.50, USD),
            quantity=10,
            commission=Money.mint(0.50, USD)
        )
        ```

    Design Notes:
        - frozen=True ensures immutability
        - kw_only=True prevents positional argument confusion
        - ABC prevents direct instantiation
        - All events must be subclasses with domain-specific fields
        - Generic TAggregateId allows type-safe IDs during migration
    """

    event_id: UUID
    occurred_at: datetime
    recorded_at: datetime
    aggregate_id: TAggregateId
    aggregate_type: str

    def __post_init__(self):
        """
        Validate required fields.

        Raises:
            ValueError / ContractError: If any required field is invalid
        """
        g.ensure_not_none(self.event_id, "event_id")

        ensure_tz_aware(self.recorded_at, "occurred_at")
        ensure_tz_aware(self.recorded_at, "recorded_at")

        g.ensure_not_none(self.aggregate_id, "aggregate_id")
        g.ensure_str_is_valued(self.aggregate_type, "aggregate_type")

    @property
    def event_type(self) -> str:
        """Get the event type name (class name)."""
        return self.__class__.__name__

    @staticmethod
    def make_metadata(aggregate_id, aggregate_type: str, occurred_at: datetime | None = None) -> dict:
        # noinspection SpellCheckingInspection
        # noinspection GrazieInspection
        """
        Helper factory for creating common event metadata fields.

        Args:
            aggregate_id: ID of the aggregate (type matches TAggregateId)
            aggregate_type: Type name of the aggregate
            occurred_at: When the event actually occurred (business time).
                        If None, defaults to now (synchronous event).
                        If provided, used for historical/migration scenarios.

        Returns:
            Dictionary with event_id, occurred_at, recorded_at, aggregate_id, aggregate_type

        Example (synchronous event):
            ```python
            # occurred_at and recorded_at both set to now
            event = TradeFilled(
                **DomainEvent.make_metadata(trade.id, "Trade"),
                trade_id=trade.id,
                fill_price=...,
            )
            ```

        Example (historical event during migration):
            ```python
            # occurred_at = 6 months ago, recorded_at = now
            event = TradeOpened(
                **DomainEvent.make_metadata(
                    trade.id,
                    "Trade",
                    occurred_at=datetime(2024, 7, 15, 10, 0, tzinfo=UTC)
                ),
                trade_id=trade.id,
                symbol="AAPL",
            )
            ```
        """
        from uuid import uuid4

        return {
            "event_id": uuid4(),
            "occurred_at": occurred_at or datetime.now(UTC),
            "recorded_at": datetime.now(UTC),
            "aggregate_id": aggregate_id,
            "aggregate_type": aggregate_type,
        }


def ensure_tz_aware(dt: datetime | None, field_name: str) -> datetime:
    """Internal helper: ensure datetime is timezone-aware (not naive)."""
    g.ensure_not_none(dt, field_name)
    if dt.tzinfo is None:
        raise ValueError(
            f"{field_name!r} must be timezone-aware (use tzinfo=UTC or similar)" # noqa
        )
    return dt