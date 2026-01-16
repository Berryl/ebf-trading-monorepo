# test_event_infrastructure.py

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from ebf_domain.events.event_collection import EventCollection
from tests.events.helpers.event_factory import SampleEvent, SampleAggregate

KNOWN_DATE = datetime(2001, 9, 11, 8, 46, 40, tzinfo=ZoneInfo('America/New_York'))


class TestEventSource:
    def test_record_creates_synchronous_event(self):
        agg = SampleAggregate(name="x")

        before = datetime.now(UTC)
        agg.record(SampleEvent, test_id="TEST-001", value=42)
        after = datetime.now(UTC)

        events = agg.peek_events()
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, SampleEvent)
        assert isinstance(event.event_id, UUID)
        assert event.aggregate_type == "SampleAggregate"
        assert before <= event.occurred_at <= after
        assert before <= event.recorded_at <= after
        assert abs((event.occurred_at - event.recorded_at).total_seconds()) < 0.1

    def test_record_can_create_historical_event(self):
        agg = SampleAggregate(name="x")
        historical = datetime(2024, 7, 15, 10, 0, tzinfo=UTC)
        before_recording = datetime.now(UTC)

        agg.record(SampleEvent, occurred_at=historical, test_id="TEST-001", value=42)

        after_recording = datetime.now(UTC)
        event = agg.peek_events()[0]

        assert event.occurred_at == historical
        assert before_recording <= event.recorded_at <= after_recording
        assert event.recorded_at > event.occurred_at

    def test_collect_events_clears_pending(self):
        agg = SampleAggregate(name="x")
        agg.record(SampleEvent, test_id="A", value=1)
        agg.record(SampleEvent, test_id="B", value=2)

        collected = agg.collect_events()
        assert len(collected) == 2
        assert agg.event_count == 0
        assert not agg.has_events


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
            event_id=uuid4(),
            occurred_at=datetime.now(UTC),
            recorded_at=datetime.now(UTC),
            aggregate_id="AGG-123",
            aggregate_type="TestAggregate",
            test_id="TEST-001",
            value=42,
        )

        events.add(event)
        assert events.has_events
        assert not events.is_empty
        assert events.count == 1
        assert len(events) == 1
        assert bool(events)

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
