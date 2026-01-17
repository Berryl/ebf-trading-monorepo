# test_event_infrastructure.py
from dataclasses import dataclass
from datetime import UTC
from uuid import UUID

import pytest

from ebf_domain.events.domain_event import DomainEvent
from ebf_domain.events.event_source import EventSource
from tests.events.helpers.event_factory import SampleEvent, KNOWN_DATE


@dataclass(eq=False)
class SampleAggregate(EventSource):
    name: str


class TestEventSource:
    @pytest.fixture
    def sut(self) -> EventSource:
        return SampleAggregate(name="X")

    @pytest.fixture
    def e(self, sut) -> DomainEvent:
        sut.record(SampleEvent, test_id="TEST-001", value=42)
        return sut.peek_events()[0]

    class TestRecordEvent:

        def test_default_metadata(self, e: DomainEvent):
            assert isinstance(e.event_id, UUID)
            assert e.aggregate_type == "SampleAggregate"
            assert e.recorded_at.tzinfo is UTC
            assert e.occurred_at.tzinfo is UTC
            assert e.recorded_at >= e.occurred_at

        def test_payload_is_preserved(self, e: SampleEvent):
            assert e.test_id == "TEST-001"
            assert e.value == 42

        def test_can_override_occurred_at(self, sut):
            sut.record(SampleEvent, occurred_at=KNOWN_DATE, test_id="TEST-001", value=42)
            e = sut.peek_events()[0]
            assert e.occurred_at == KNOWN_DATE

    class TestCollectEvents:

        def test_all_events_are_returned_and_cleared_internally(self, sut):
            sut.record(SampleEvent, test_id="A", value=1)
            sut.record(SampleEvent, test_id="B", value=2)
            assert sut.event_count == 2

            events = sut.collect_events()
            assert len(events) == 2

            assert sut.event_count == 0
            assert not sut.has_events
