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
        occurred_at: When the event occurred (UTC timezone-aware)
        aggregate_id: ID of the aggregate that raised this event (type-safe)
        aggregate_type: Type name of the aggregate (for routing/filtering)

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

        # Create event with factory helper
        event = TradeFilled(
            **DomainEvent.make_metadata("TRADE-123", "Trade"),
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
    aggregate_id: TAggregateId
    aggregate_type: str

    def __post_init__(self):
        """
        Validate required fields.

        Raises:
            ValueError / ContractError: If any required field is invalid
        """
        g.ensure_not_none(self.event_id, "event_id")
        g.ensure_not_none(self.occurred_at, "occurred_at")
        if not self.occurred_at.tzinfo:
            raise ValueError("occurred_at must be timezone-aware (use UTC)")
        g.ensure_not_none(self.aggregate_id, "aggregate_id")
        g.ensure_str_is_valued(self.aggregate_type, "aggregate_type")

    @property
    def event_type(self) -> str:
        """Get the event type name (class name)."""
        return self.__class__.__name__

    @staticmethod
    def make_metadata(aggregate_id, aggregate_type: str) -> dict:
        """
        Helper factory for creating common event metadata fields.

        Args:
            aggregate_id: ID of the aggregate (type matches TAggregateId)
            aggregate_type: Type name of the aggregate

        Returns:
            Dictionary with event_id, occurred_at, aggregate_id, aggregate_type

        Example:
            ```python
            event = TradeFilled(
                **DomainEvent.make_metadata(trade.id, "Trade"),
                trade_id=trade.id,
                # ... other fields
            )
            ```
        """
        from uuid import uuid4

        return {
            "event_id": uuid4(),
            "occurred_at": datetime.now(UTC),
            "aggregate_id": aggregate_id,
            "aggregate_type": aggregate_type,
        }
