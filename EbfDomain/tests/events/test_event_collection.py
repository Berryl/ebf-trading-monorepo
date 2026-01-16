from datetime import datetime, UTC, timedelta

import pytest

from ebf_domain.events.domain_event import DomainEvent
from ebf_domain.events.event_collection import EventCollection
from tests.events.helpers.event_factory import SampleEvent, make_event, KNOWN_DATE


class TestEventCollection:

    @pytest.fixture
    def sut(self) -> EventCollection:
        return EventCollection()

    # region helper fixtures
    @pytest.fixture
    def now(self) -> datetime:
        return datetime.now(UTC)

    @pytest.fixture
    def yesterday(self, now) -> datetime:
        return now - timedelta(days=1)

    @pytest.fixture
    def tomorrow(self, now) -> datetime:
        return now + timedelta(days=1)

    @pytest.fixture
    def event_list(self, sut, yesterday, now, tomorrow) -> list:
        e1 = make_event(SampleEvent, test_id="1", value=1, occurred_at=yesterday)
        e2 = make_event(SampleEvent, test_id="2", value=2, occurred_at=now)
        e3 = make_event(SampleEvent, test_id="3", value=3, occurred_at=tomorrow)
        return [e1, e2, e3]

    @pytest.fixture
    def sut_with_events(self, sut, event_list) -> EventCollection:
        return sut.add_all(event_list)

    # endregion

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

        def test_can_add_by_chaining(self, sut):
            e1 = make_event(SampleEvent, test_id="1", value=1)
            e2 = make_event(SampleEvent, test_id="2", value=2)
            e3 = make_event(SampleEvent, test_id="3", value=3)
            sut.add(e1).add(e2).add(e3)

            assert sut.count == 3
            assert len(sut) == 3

            assert sut.count == 3

        def test_can_add_list(self, sut, event_list: list):
            sut.add_all(event_list)

            assert sut.count == len(event_list)

    class TestListOps:

        def test_can_get_first(self, sut_with_events, event_list: list):
            assert sut_with_events.first() == event_list[0]

        def test_can_get_last(self, sut_with_events, event_list: list):
            assert sut_with_events.last() == event_list[2]

        def test_can_get_list(self, sut_with_events, event_list: list):
            assert sut_with_events.to_list() == event_list

        def test_can_iterate(self, sut_with_events):
            item: SampleEvent
            k = 1
            for item in sut_with_events:
                assert item.value == k
                k += 1

    class TestFiltering:

        class TestTimeFilters:

            def test_can_get_before_date(self, sut_with_events, now, yesterday):
                result: DomainEvent = sut_with_events.before(now).first()
                assert result.occurred_at == yesterday

            def test_can_get_after_date(self, sut_with_events, now, tomorrow):
                result: DomainEvent = sut_with_events.after(now).first()
                assert result.occurred_at == tomorrow

#
#
# def test_can_chain_multiple_filters(self):
#     sut = EventCollection()
#     now = datetime.now(UTC)
#     yesterday =
#     tomorrow = now + timedelta(days=1)
#
#     e1 = make_event(SampleEvent, test_id="OLD", value=1, occurred_at=yesterday)
#     e2 = make_event(SampleEvent, test_id="NOW", value=2, occurred_at=now)
#     e3 = make_event(SampleEvent, test_id="FUTURE", value=3, occurred_at=tomorrow)
#     sut.add(e1).add(e2).add(e3)
#
#     result = sut.of_type(SampleEvent).after(yesterday).for_aggregate("AGG-123")
#
#     assert result.count == 1
#     event = result.first()
#     assert event.test_id == "NOW"
