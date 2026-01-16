from datetime import datetime, UTC, timedelta

import pytest

from ebf_domain.events.domain_event import DomainEvent
from ebf_domain.events.event_collection import EventCollection
from tests.events.helpers.event_factory import SampleEvent, make_event, KNOWN_DATE, AnotherEvent


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

        class TestFilterByTime:

            def test_can_get_before_date(self, sut_with_events, now, yesterday):
                result: DomainEvent = sut_with_events.before(now).first()
                assert result.occurred_at == yesterday

            def test_can_get_after_date(self, sut_with_events, now, tomorrow):
                result: DomainEvent = sut_with_events.after(now).first()
                assert result.occurred_at == tomorrow

        class TestFilterByType:
            @pytest.fixture
            def sut_with_mixed_types(self, sut_with_events) -> EventCollection:
                e1 = make_event(AnotherEvent, test_id="100", description="one")
                e2 = make_event(AnotherEvent, test_id="200", description="two")
                e3 = make_event(AnotherEvent, test_id="300", description="three")
                sut_with_events.add(e1).add(e2).add(e3)

                return sut_with_events

            def test_can_get_by_type(self, sut_with_mixed_types):
                assert sut_with_mixed_types.count == 6

                assert sut_with_mixed_types.of_type(AnotherEvent).count == 3
                assert sut_with_mixed_types.of_type(SampleEvent).count == 3

        class TestFilterByAggregate:
            @pytest.fixture
            def sut_with_mixed_types(self, sut_with_events) -> EventCollection:
                e1 = make_event(AnotherEvent, test_id="100", description="one")
                e2 = make_event(AnotherEvent, test_id="200", description="two")
                e3 = make_event(AnotherEvent, test_id="300", description="three")
                sut_with_events.add(e1).add(e2).add(e3)
