from datetime import datetime, UTC
from uuid import uuid4

import pytest
from ebf_core.guards.guards import ContractError

from tests.events.helpers.event_factory import make_event, SampleEvent, make_degenerate_event, KNOWN_DATE


class TestDomainEvent:

    def test_immutability(self):
        sut = make_event(SampleEvent, test_id="TEST-001", value=42, occurred_at=KNOWN_DATE)

        with pytest.raises(Exception):
            sut.occurred_at = datetime.now(UTC)  # noqa base properties are immutable
        with pytest.raises(Exception):
            sut.value = 99  # noqa inheriteded properties are also immutable

    def test_equality(self):
        known_id = uuid4()
        e1 = make_event(SampleEvent, test_id="TEST-001", value=42,
                        event_id=known_id, occurred_at=KNOWN_DATE, recorded_at=KNOWN_DATE)
        e2 = make_event(SampleEvent, test_id="TEST-001", value=42,
                        event_id=known_id, occurred_at=KNOWN_DATE, recorded_at=KNOWN_DATE)
        e3 = make_event(SampleEvent, test_id="TEST-001", value=42, event_id=known_id, occurred_at=datetime.now(UTC))

        assert e1 != e3
        assert hash(e1) != hash(e3)

        assert e1 == e2
        assert hash(e1) == hash(e2)

    class TestPropertyGuards:

        def test_event_type_property_is_class_name(self):
            sut = make_event(SampleEvent, test_id="TEST-001", value=42)
            assert sut.event_type == "SampleEvent"

        def test_event_id_cannot_be_none(self):
            with pytest.raises(ContractError, match="'event_id' cannot be None"):
                make_degenerate_event(SampleEvent, event_id=None)

        def test_occurred_at_cannot_be_none(self):
            with pytest.raises(ContractError, match="'occurred_at' cannot be None"):
                make_degenerate_event(SampleEvent, event_id=uuid4(), occurred_at=None)

        def test_occurred_at_must_be_timezone_aware(self):
            with pytest.raises(ValueError, match="'occurred_at' must be timezone-aware"):
                make_degenerate_event(SampleEvent, event_id=uuid4(), occurred_at=datetime.now())

        def test_recorded_at_cannot_be_none(self):
            with pytest.raises(ContractError, match="'recorded_at' cannot be None"):
                make_degenerate_event(
                    SampleEvent, event_id=uuid4(), occurred_at=datetime.now(UTC), recorded_at=None)

        def test_recorded_at_must_be_timezone_aware(self):
            with pytest.raises(ValueError, match="'recorded_at' must be timezone-aware"):
                make_event(SampleEvent, recorded_at=datetime.now())

        def test_aggregate_type_must_be_valued(self):
            with pytest.raises(ContractError, match="'aggregate_type' cannot be an empty string"):
                make_event(SampleEvent, aggregate_type="   ")
