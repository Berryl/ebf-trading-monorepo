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

    def test_aggregate_type_is_class_name(self, sut):
        assert sut.aggregate_type == "SampleAggregate"

    class TestRecordEvent:

        def test_pending_events_are_added_to(self, sut):
            assert sut.has_events is False
            assert sut.event_count == 0

            sut.record(SampleEvent, test_id="TEST-RECORD-ADDS-EVENT", value=0)
            assert sut.has_events
            assert sut.event_count == 1

        def test_peek_events_returns_a_list_of_pending_events(self, sut):
            sut.record(SampleEvent, test_id="TEST-PEEK-EVENTS", value=42)

            result = sut.peek_events()

            assert isinstance(result, list)
            assert isinstance(result[0], DomainEvent)
            assert result[0].test_id == "TEST-PEEK-EVENTS"

        def test_can_override_occurred_at(self, sut):
            sut.record(SampleEvent, occurred_at=KNOWN_DATE, test_id="TEST-001", value=42)
            e = sut.peek_events()[0]
            assert e.occurred_at == KNOWN_DATE

        class TestEventMetadata:

            @pytest.fixture
            def e(self, sut) -> DomainEvent:
                sut.record(SampleEvent, test_id="TEST-001", value=42)
                return sut.peek_events()[0]

            def test_default_metadata(self, e: DomainEvent):
                assert isinstance(e.event_id, UUID)
                assert e.aggregate_type == "SampleAggregate"
                assert e.recorded_at.tzinfo is UTC
                assert e.occurred_at.tzinfo is UTC
                assert e.recorded_at >= e.occurred_at

            def test_payload_is_preserved(self, e: SampleEvent):
                assert e.test_id == "TEST-001"
                assert e.value == 42

    class TestCollectEvents:

        def test_all_events_are_returned_and_cleared_internally(self, sut):
            sut.record(SampleEvent, test_id="A", value=1)
            sut.record(SampleEvent, test_id="B", value=2)
            assert sut.event_count == 2

            events = sut.collect_events()
            assert len(events) == 2

            assert sut.event_count == 0
            assert not sut.has_events

    class TestAggregateIdCorrelation:
        """Tests for aggregate_id_for_events behavior with IDBase[T] integration."""

        def test_tbd_aggregate_uses_temporary_uuid_for_correlation(self, sut: SampleAggregate):
            # TBD aggregate gets temporary correlation ID
            sut.record(SampleEvent, test_id="BEFORE", value=1)
            event = sut.peek_events()[0]

            assert isinstance(event.aggregate_id, UUID)
            temp_correlation_id = event.aggregate_id

            # Subsequent events use same temporary correlation ID
            sut.record(SampleEvent, test_id="ALSO-BEFORE", value=2)
            event2 = sut.peek_events()[1]
            assert event2.aggregate_id == temp_correlation_id

        def test_resolved_aggregate_uses_business_id_for_correlation(self, sut: SampleAggregate):
            # Record event while TBD
            sut.record(SampleEvent, test_id="BEFORE", value=1)
            temp_id = sut.peek_events()[0].aggregate_id

            # Simulate ID resolution (as IDBase[T] would do)
            sut.id_value = "AGG-RESOLVED-001"

            # After resolution, events use business ID for correlation
            sut.record(SampleEvent, test_id="AFTER", value=2)
            event_after = sut.peek_events()[1]

            assert event_after.aggregate_id == "AGG-RESOLVED-001"
            assert event_after.aggregate_id != temp_id

        def test_correlation_id_is_consistent_within_lifecycle(self, sut: SampleAggregate):
            """All events from the same aggregate instance share correlation ID."""
            sut.id_value = "AGG-123"  # Already resolved

            # Multiple events should all use the same correlation ID
            sut.record(SampleEvent, test_id="E1", value=1)
            sut.record(SampleEvent, test_id="E2", value=2)
            sut.record(SampleEvent, test_id="E3", value=3)

            events = sut.peek_events()
            correlation_ids = {e.aggregate_id for e in events}

            assert len(correlation_ids) == 1
            assert "AGG-123" in correlation_ids