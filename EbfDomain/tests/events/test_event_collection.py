from datetime import datetime, UTC, timedelta

import pytest

from ebf_domain.events.event_collection import EventCollection
from tests.events.helpers.event_factory import SampleEvent, make_event, KNOWN_DATE


class TestEventCollection:

    @pytest.fixture
    def sut(self)-> EventCollection:
        return EventCollection()

    def test_creation_is_empty(self, sut):
        assert sut.is_empty
        assert not sut.has_events
        assert sut.count == 0

        assert len(sut) == 0
        assert not bool(sut)

    class TestAdding:

        def test_can_add_single_event(self, sut):
            e = make_event(SampleEvent, test_id="TEST-001", value=42, occurred_at=KNOWN_DATE)
            sut.add(e)

            assert sut.has_events
            assert not sut.is_empty
            assert sut.count == 1
            assert len(sut) == 1
            assert bool(sut)

        def test_can_add_by_chaining(self):
            sut = EventCollection()

            e1 = make_event(SampleEvent, test_id="1", value=1)
            e2 = make_event(SampleEvent, test_id="2", value=2)
            e3 = make_event(SampleEvent, test_id="3", value=3)
            sut.add(e1).add(e2).add(e3)

            assert sut.count == 3
            assert len(sut) == 3


def test_can_chain_multiple_filters(self):
    sut = EventCollection()
    now = datetime.now(UTC)
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)

    e1 = make_event(SampleEvent, test_id="OLD", value=1, occurred_at=yesterday)
    e2 = make_event(SampleEvent, test_id="NOW", value=2, occurred_at=now)
    e3 = make_event(SampleEvent, test_id="FUTURE", value=3, occurred_at=tomorrow)
    sut.add(e1).add(e2).add(e3)

    result = sut.of_type(SampleEvent).after(yesterday).for_aggregate("AGG-123")

    assert result.count == 1
    event = result.first()
    assert event.test_id == "NOW"
