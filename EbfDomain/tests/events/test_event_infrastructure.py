"""
Tests for core domain event infrastructure.
"""

import pytest
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from ebf_core.guards.guards import ContractError

from src.ebf_domain.events.domain_event import DomainEvent
from src.ebf_domain.events.event_collection import EventCollection


# Test event for demonstrations
@dataclass(frozen=True, kw_only=True)
class TestEvent(DomainEvent[str]):
    """Simple test event."""

    test_id: str
    value: int


@dataclass(frozen=True, kw_only=True)
class AnotherEvent(DomainEvent[str]):
    """Another test event type."""

    test_id: str
    description: str


class TestDomainEvent:
    """Tests for DomainEvent base class."""

    def test_create_event_with_metadata_helper(self):
        """Can create event using make_metadata helper."""
        event = TestEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )

        assert event.aggregate_id == "AGG-123"
        assert event.aggregate_type == "TestAggregate"
        assert isinstance(event.event_id, UUID)
        assert event.occurred_at.tzinfo is not None  # Timezone-aware
        assert event.test_id == "TEST-001"
        assert event.value == 42

    def test_event_type_property(self):
        """event_type returns class name."""
        event = TestEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )

        assert event.event_type == "TestEvent"

    def test_events_are_immutable(self):
        """Events are frozen and cannot be modified."""
        event = TestEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.value = 99 # noqa

    def test_event_equality_by_structure(self):
        """Events are equal if all fields match (structural equality)."""
        event_id = uuid4()
        timestamp = datetime.now(UTC)

        event1 = TestEvent(
            event_id=event_id,
            occurred_at=timestamp,
            aggregate_id="AGG-123",
            aggregate_type="TestAggregate",
            test_id="TEST-001",
            value=42,
        )

        event2 = TestEvent(
            event_id=event_id,
            occurred_at=timestamp,
            aggregate_id="AGG-123",
            aggregate_type="TestAggregate",
            test_id="TEST-001",
            value=42,
        )

        assert event1 == event2
        assert hash(event1) == hash(event2)

    def test_validation_rejects_none_event_id(self):
        """Cannot create event with None event_id."""
        with pytest.raises(ContractError, match="cannot be None"):
            TestEvent(
                event_id=None,
                occurred_at=datetime.now(UTC),
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )

    def test_validation_rejects_none_occurred_at(self):
        """Cannot create event with None occurred_at."""
        with pytest.raises(ContractError, match="cannot be None"):
            TestEvent(
                event_id=uuid4(),
                occurred_at=None,
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )

    def test_validation_rejects_naive_datetime(self):
        """Cannot create event with timezone-naive datetime."""
        with pytest.raises(ValueError, match="must be timezone-aware"):
            TestEvent(
                event_id=uuid4(),
                occurred_at=datetime.now(),  # No timezone!
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )

    def test_validation_rejects_empty_aggregate_type(self):
        """Cannot create event with empty aggregate_type."""
        with pytest.raises(ContractError, match="cannot be an empty string"):
            TestEvent(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                aggregate_id="AGG-123",
                aggregate_type="",
                test_id="TEST-001",
                value=42,
            )


class TestEventCollection:
    """Tests for EventCollection."""

    def test_create_empty_collection(self):
        """Can create empty event collection."""
        events = EventCollection()

        assert events.is_empty
        assert not events.has_events
        assert events.count == 0
        assert len(events) == 0
        assert not bool(events)

    def test_add_event(self):
        """Can add event to collection."""
        events = EventCollection()
        event = TestEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )

        events.add(event)

        assert events.has_events
        assert not events.is_empty
        assert events.count == 1
        assert len(events) == 1
        assert bool(events)

    def test_add_multiple_events(self):
        """Can add multiple events."""
        events = EventCollection()
        event1 = TestEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=1,
        )
        event2 = TestEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-002",
            value=2,
        )

        events.add(event1)
        events.add(event2)

        assert events.count == 2

    def test_add_all(self):
        """Can add multiple events at once."""
        events = EventCollection()
        event_list = [
            TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id=f"TEST-{i}", value=i)
            for i in range(5)
        ]

        events.add_all(event_list)

        assert events.count == 5

    def test_of_type_filters_by_type(self):
        """of_type returns only events of specified type."""
        events = EventCollection()
        test_event = TestEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )
        another_event = AnotherEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-002",
            description="hello",
        )

        events.add(test_event)
        events.add(another_event)

        test_events = events.of_type(TestEvent)

        assert test_events.count == 1
        assert isinstance(test_events.first(), TestEvent)

    def test_of_type_returns_event_collection(self):
        """of_type returns EventCollection for chaining."""
        events = EventCollection()
        events.add(TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=42))

        result = events.of_type(TestEvent)

        assert isinstance(result, EventCollection)

    def test_filter_chaining(self):
        """Can chain multiple filters."""
        events = EventCollection()
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        # Add events at different times
        events.add(
            TestEvent(
                event_id=uuid4(),
                occurred_at=yesterday,
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="OLD",
                value=1,
            )
        )
        events.add(
            TestEvent(
                event_id=uuid4(),
                occurred_at=now,
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="NOW",
                value=2,
            )
        )
        events.add(
            TestEvent(
                event_id=uuid4(),
                occurred_at=tomorrow,
                aggregate_id="AGG-456",
                aggregate_type="TestAggregate",
                test_id="FUTURE",
                value=3,
            )
        )

        # Chain filters
        result = events.of_type(TestEvent).after(yesterday).for_aggregate("AGG-123")

        assert result.count == 1
        event = result.first()
        assert event.test_id == "NOW"

    def test_first_and_last(self):
        """Can get first and last events."""
        events = EventCollection()

        # Empty collection
        assert events.first() is None
        assert events.last() is None

        # Add events
        event1 = TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="FIRST", value=1)
        event2 = TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="LAST", value=2)
        events.add(event1)
        events.add(event2)

        assert events.first().test_id == "FIRST"
        assert events.last().test_id == "LAST"

    def test_to_list_returns_copy(self):
        """to_list returns a defensive copy."""
        events = EventCollection()
        event = TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=42)
        events.add(event)

        event_list = events.to_list()

        # Modifying the list doesn't affect the collection
        event_list.clear()
        assert events.count == 1

    def test_clear(self):
        """Can clear all events."""
        events = EventCollection()
        events.add(TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=42))
        assert events.count == 1

        events.clear()

        assert events.is_empty
        assert events.count == 0

    def test_iteration(self):
        """Can iterate over events."""
        events = EventCollection()
        event_list = [
            TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id=f"TEST-{i}", value=i)
            for i in range(3)
        ]
        events.add_all(event_list)

        collected = list(events)

        assert len(collected) == 3
        assert all(isinstance(e, TestEvent) for e in collected)

    def test_where_custom_predicate(self):
        """Can filter with custom predicate."""
        events = EventCollection()
        events.add(TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=10))
        events.add(TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-002", value=50))
        events.add(TestEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-003", value=100))

        high_value = events.where(lambda e: isinstance(e, TestEvent) and e.value > 40)

        assert high_value.count == 2
        assert all(e.value > 40 for e in high_value)
