from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from ebf_core.guards.guards import ContractError

from ebf_domain.events.domain_event import DomainEvent
from ebf_domain.events.event_collection import EventCollection


@dataclass(frozen=True, kw_only=True)
class SampleEvent(DomainEvent[str]):
    test_id: str
    value: int


@dataclass(frozen=True, kw_only=True)
class AnotherEvent(DomainEvent[str]):
    test_id: str
    description: str


class TestDomainEvent:

    def test_make_metadata_helper_creates_synchronous_event(self):
        before = datetime.now(UTC)
        
        event = SampleEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )
        
        after = datetime.now(UTC)

        assert event.aggregate_id == "AGG-123"
        assert event.aggregate_type == "TestAggregate"
        assert isinstance(event.event_id, UUID)
        assert event.occurred_at.tzinfo is not None
        assert event.recorded_at.tzinfo is not None
        assert event.test_id == "TEST-001"
        assert event.value == 42
        
        # Synchronous event: timestamps should be nearly identical
        assert before <= event.occurred_at <= after
        assert before <= event.recorded_at <= after
        assert abs((event.occurred_at - event.recorded_at).total_seconds()) < 0.1

    def test_event_type_property_returns_class_name(self):
        event = SampleEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )

        assert event.event_type == "SampleEvent"

    def test_events_are_immutable_after_creation(self):
        event = SampleEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=42,
        )

        with pytest.raises(Exception):  # FrozenInstanceError
            event.value = 99  # noqa

    def test_events_equal_when_all_fields_match(self):
        event_id = uuid4()
        occurred_timestamp = datetime(2025, 1, 15, 10, 0, tzinfo=UTC)
        recorded_timestamp = datetime(2025, 1, 15, 10, 1, tzinfo=UTC)

        event1 = SampleEvent(
            event_id=event_id,
            occurred_at=occurred_timestamp,
            recorded_at=recorded_timestamp,
            aggregate_id="AGG-123",
            aggregate_type="TestAggregate",
            test_id="TEST-001",
            value=42,
        )

        event2 = SampleEvent(
            event_id=event_id,
            occurred_at=occurred_timestamp,
            recorded_at=recorded_timestamp,
            aggregate_id="AGG-123",
            aggregate_type="TestAggregate",
            test_id="TEST-001",
            value=42,
        )

        assert event1 == event2
        assert hash(event1) == hash(event2)

    def test_rejects_none_event_id(self):
        with pytest.raises(ContractError, match="cannot be None"):
            SampleEvent(
                event_id=None,
                occurred_at=datetime.now(UTC),
                recorded_at=datetime.now(UTC),
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )

    def test_rejects_none_occurred_at(self):
        with pytest.raises(ContractError, match="cannot be None"):
            SampleEvent(
                event_id=uuid4(),
                occurred_at=None,
                recorded_at=datetime.now(UTC),
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )

    def test_rejects_naive_occurred_at_datetime(self):
        with pytest.raises(ValueError, match="must be timezone-aware"):
            SampleEvent(
                event_id=uuid4(),
                occurred_at=datetime.now(),  # No timezone
                recorded_at=datetime.now(UTC),
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )

    def test_rejects_empty_aggregate_type(self):
        with pytest.raises(ContractError, match="cannot be an empty string"):
            SampleEvent(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                recorded_at=datetime.now(UTC),
                aggregate_id="AGG-123",
                aggregate_type="",
                test_id="TEST-001",
                value=42,
            )

    def test_can_create_historical_event_with_past_occurred_at(self):
        historical_time = datetime(2024, 7, 15, 10, 0, tzinfo=UTC)
        before_recording = datetime.now(UTC)

        event = SampleEvent(
            **DomainEvent.make_metadata(
                "AGG-123", "TestAggregate", occurred_at=historical_time
            ),
            test_id="TEST-001",
            value=42,
        )

        after_recording = datetime.now(UTC)

        assert event.occurred_at == historical_time
        assert before_recording <= event.recorded_at <= after_recording
        assert event.recorded_at > event.occurred_at

    def test_rejects_none_recorded_at(self):
        with pytest.raises(ContractError, match="cannot be None"):
            SampleEvent(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                recorded_at=None,
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )

    def test_rejects_naive_recorded_at_datetime(self):
        with pytest.raises(ValueError, match="must be timezone-aware"):
            SampleEvent(
                event_id=uuid4(),
                occurred_at=datetime.now(UTC),
                recorded_at=datetime.now(),  # No timezone
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="TEST-001",
                value=42,
            )


class TestEventCollection:

    def test_empty_collection_has_no_events(self):
        events = EventCollection()

        assert events.is_empty
        assert not events.has_events
        assert events.count == 0
        assert len(events) == 0
        assert not bool(events)

    def test_can_add_single_event(self):
        events = EventCollection()
        event = SampleEvent(
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

    def test_can_add_multiple_events_sequentially(self):
        events = EventCollection()
        event1 = SampleEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-001",
            value=1,
        )
        event2 = SampleEvent(
            **DomainEvent.make_metadata("AGG-123", "TestAggregate"),
            test_id="TEST-002",
            value=2,
        )

        events.add(event1)
        events.add(event2)

        assert events.count == 2

    def test_add_all_accepts_list_of_events(self):
        events = EventCollection()
        event_list = [
            SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id=f"TEST-{i}", value=i)
            for i in range(5)
        ]

        events.add_all(event_list)

        assert events.count == 5

    def test_of_type_filters_by_event_class(self):
        events = EventCollection()
        test_event = SampleEvent(
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

        test_events = events.of_type(SampleEvent)

        assert test_events.count == 1
        assert isinstance(test_events.first(), SampleEvent)

    def test_of_type_returns_event_collection_for_chaining(self):
        events = EventCollection()
        events.add(SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=42))

        result = events.of_type(SampleEvent)

        assert isinstance(result, EventCollection)

    def test_can_chain_multiple_filters(self):
        events = EventCollection()
        now = datetime.now(UTC)
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        events.add(
            SampleEvent(
                event_id=uuid4(),
                occurred_at=yesterday,
                recorded_at=now,
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="OLD",
                value=1,
            )
        )
        events.add(
            SampleEvent(
                event_id=uuid4(),
                occurred_at=now,
                recorded_at=now,
                aggregate_id="AGG-123",
                aggregate_type="TestAggregate",
                test_id="NOW",
                value=2,
            )
        )
        events.add(
            SampleEvent(
                event_id=uuid4(),
                occurred_at=tomorrow,
                recorded_at=now,
                aggregate_id="AGG-456",
                aggregate_type="TestAggregate",
                test_id="FUTURE",
                value=3,
            )
        )

        result = events.of_type(SampleEvent).after(yesterday).for_aggregate("AGG-123")

        assert result.count == 1
        event = result.first()
        assert event.test_id == "NOW"

    def test_first_returns_first_event_or_none_if_empty(self):
        events = EventCollection()

        assert events.first() is None
        assert events.last() is None

        event1 = SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="FIRST", value=1)
        event2 = SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="LAST", value=2)
        events.add(event1)
        events.add(event2)

        assert events.first().test_id == "FIRST"
        assert events.last().test_id == "LAST"

    def test_to_list_returns_defensive_copy(self):
        events = EventCollection()
        event = SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=42)
        events.add(event)

        event_list = events.to_list()
        event_list.clear()

        assert events.count == 1

    def test_clear_removes_all_events(self):
        events = EventCollection()
        events.add(SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=42))
        assert events.count == 1

        events.clear()

        assert events.is_empty
        assert events.count == 0

    def test_collection_is_iterable(self):
        events = EventCollection()
        event_list = [
            SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id=f"TEST-{i}", value=i)
            for i in range(3)
        ]
        events.add_all(event_list)

        collected = list(events)

        assert len(collected) == 3
        assert all(isinstance(e, SampleEvent) for e in collected)

    def test_where_filters_with_custom_predicate(self):
        events = EventCollection()
        events.add(SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-001", value=10))
        events.add(SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-002", value=50))
        events.add(SampleEvent(**DomainEvent.make_metadata("AGG-123", "TestAggregate"), test_id="TEST-003", value=100))

        high_value = events.where(lambda e: isinstance(e, SampleEvent) and e.value > 40)

        assert high_value.count == 2
        assert all(e.value > 40 for e in high_value)