# test_event_infrastructure.py
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import pytest

from ebf_domain.events.event_source import EventSource
from tests.events.helpers.event_factory import SampleEvent



@dataclass(eq=False)
class SampleAggregate(EventSource):
    name: str

class TestEventSource:
    @pytest.fixture
    def sut(self) -> EventSource:
        return SampleAggregate(name="X")

    @pytest.fixture
    def synchronous_event(self, sut) -> SampleEvent:
        pass

    def test_record_creates_synchronous_event(self, sut):
        before = datetime.now(UTC)
        sut.record(SampleEvent, test_id="TEST-001", value=42)
        after = datetime.now(UTC)

        events = sut.peek_events()
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
