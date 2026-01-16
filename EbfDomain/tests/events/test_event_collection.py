from datetime import datetime, UTC, timedelta
from uuid import uuid4

from ebf_domain.events.event_collection import EventCollection
from tests.events.helpers.event_factory import SampleEvent, make_event, KNOWN_DATE


class TestEventCollection:
    def test_creation_is_empty(self):
        sut = EventCollection()

        assert sut.is_empty
        assert not sut.has_events
        assert sut.count == 0

        assert len(sut) == 0
        assert not bool(sut)

    def test_can_add_single_event(self):
        sut = EventCollection()

        e = make_event(SampleEvent, test_id="TEST-001", value=42, occurred_at=KNOWN_DATE)
        sut.add(e)

        assert sut.has_events
        assert not sut.is_empty
        assert sut.count == 1
        assert len(sut) == 1
        assert bool(sut)

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
