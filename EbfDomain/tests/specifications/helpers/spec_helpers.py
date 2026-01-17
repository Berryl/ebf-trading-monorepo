"""
Test helpers for specification testing.
"""

from dataclasses import dataclass
from enum import Enum

from src.ebf_domain.specifications.specification import Specification


class ItemStatus(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    CLOSED = "closed"


@dataclass
class SampleItem:
    """Simple domain object for testing specifications."""

    name: str
    value: int
    status: ItemStatus
    tags: list[str]


# Concrete specifications for testing

class IsActive(Specification[SampleItem]):
    def is_satisfied_by(self, candidate: SampleItem) -> bool:
        return candidate.status == ItemStatus.ACTIVE

    def __repr__(self) -> str:
        return "IsActive()"


class IsClosed(Specification[SampleItem]):
    def is_satisfied_by(self, candidate: SampleItem) -> bool:
        return candidate.status == ItemStatus.CLOSED

    def __repr__(self) -> str:
        return "IsClosed()"


class IsPending(Specification[SampleItem]):
    def is_satisfied_by(self, candidate: SampleItem) -> bool:
        return candidate.status == ItemStatus.PENDING

    def __repr__(self) -> str:
        return "IsPending()"


class ValueGreaterThan(Specification[SampleItem]):
    def __init__(self, threshold: int):
        self.threshold = threshold

    def is_satisfied_by(self, candidate: SampleItem) -> bool:
        return candidate.value > self.threshold

    def __repr__(self) -> str:
        return f"ValueGreaterThan({self.threshold})"


class ValueLessThan(Specification[SampleItem]):
    def __init__(self, threshold: int):
        self.threshold = threshold

    def is_satisfied_by(self, candidate: SampleItem) -> bool:
        return candidate.value < self.threshold

    def __repr__(self) -> str:
        return f"ValueLessThan({self.threshold})"


class NameStartsWith(Specification[SampleItem]):
    def __init__(self, prefix: str):
        self.prefix = prefix

    def is_satisfied_by(self, candidate: SampleItem) -> bool:
        return candidate.name.startswith(self.prefix)

    def __repr__(self) -> str:
        return f"NameStartsWith('{self.prefix}')"


class HasTag(Specification[SampleItem]):
    def __init__(self, tag: str):
        self.tag = tag

    def is_satisfied_by(self, candidate: SampleItem) -> bool:
        return self.tag in candidate.tags

    def __repr__(self) -> str:
        return f"HasTag('{self.tag}')"


# Factory helpers

def make_item(
    name: str = "TestItem",
    value: int = 50,
    status: ItemStatus = ItemStatus.ACTIVE,
    tags: list[str] | None = None,
) -> SampleItem:
    """Create a sample item for testing."""
    return SampleItem(name=name, value=value, status=status, tags=tags or [])