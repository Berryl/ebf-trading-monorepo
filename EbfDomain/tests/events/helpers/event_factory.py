# tests/helpers/event_factory.py
"""
Test-only helpers for constructing domain events.

This module exists to support *unit testing of event classes in isolation*,
without involving aggregates or EventSource metadata stamping.

Key points:
- These helpers are NOT part of the production eventing API.
- They intentionally bypass EventSource to reduce test noise when validating:
    - event immutability
    - equality / hashing
    - field validation
    - serialization behavior
- Production code should always create events via EventSource.record(...).

If a test cares about aggregate behavior or event metadata correctness,
it should use a real aggregate and EventSource instead of this helper.
"""
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Type
from uuid import uuid4, UUID

from ebf_domain.events.domain_event import DomainEvent
from ebf_domain.events.event_source import EventSource


def make_event(event_type: Type[DomainEvent], *,
               event_id: UUID | None = None,
               aggregate_id="AGG-123",
               aggregate_type="TestAggregate",
               occurred_at: datetime | None = None,
               recorded_at: datetime | None = None,
               **payload,
               ):
    """
    Test-only factory for constructing fully stamped domain events.

    This helper is intended for unit tests that validate event classes
    (equality, validation, immutability) without setting up an aggregate.

    Production code must not use this helper; events should be created
    via EventSource.record(...) so that metadata is stamped consistently.
    """
    now = datetime.now(UTC)
    return event_type(
        event_id=event_id or uuid4(),
        occurred_at=occurred_at or now,
        recorded_at=recorded_at or now,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        **payload,
    )


def make_degenerate_event(event_type: Type[DomainEvent], *,
               event_id: UUID | None = None,
               aggregate_id="AGG-123",
               aggregate_type="TestAggregate",
               occurred_at: datetime | None = None,
               recorded_at: datetime | None = None,
               **payload,
               ):
    """
    Thin wrapper to test post-init guards
    """
    now = datetime.now(UTC)
    return event_type(
        event_id=event_id,
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        aggregate_id=aggregate_id,
        aggregate_type=aggregate_type,
        **payload,
    )


@dataclass(frozen=True, kw_only=True)
class SampleEvent(DomainEvent[object]):
    test_id: str = "TEST-001"
    value: int = 42


@dataclass(frozen=True, kw_only=True)
class AnotherEvent(DomainEvent[object]):
    test_id: str
    description: str


@dataclass(eq=False)
class SampleAggregate(EventSource):
    name: str
