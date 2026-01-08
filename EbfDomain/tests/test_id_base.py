import uuid
from dataclasses import dataclass

import pytest

from src.id_base import IDBase

"""Tests demonstrating that a single generic entity class can safely use different ID types."""

# ONE single domain class — reused for all ID types
@dataclass(eq=False)
class Person[T](IDBase[T]):
    """A person entity that can have str, UUID, or int IDs depending on T."""
    name: str
    age: int
    email: str = ""


# -----------------------------
# Tests with str IDs (e.g., legacy system)
# -----------------------------
class TestPersonWithStrId:
    def test_lifecycle_with_str_id(self):
        person = Person(name="Alice", age=30)
        assert person.is_tbd
        with pytest.raises(ValueError):
            _ = person.id

        person.resolve_id("PER-001")  # str ID

        assert not person.is_tbd
        assert person.id == "PER-001"
        assert isinstance(person.id, str)

        # Cannot reassign
        with pytest.raises(ValueError):
            person.resolve_id("PER-999")

    def test_equality_with_str(self):
        p1 = Person(name="Bob", age=25)
        p2 = Person(name="Bob", age=25)

        p1.resolve_id("PER-123")
        p2.resolve_id("PER-123")

        assert p1 == p2
        assert hash(p1) == hash(p2)

        p3 = Person(name="Bob", age=25)
        p3.resolve_id("PER-999")
        assert p1 != p3


# -----------------------------
# Tests with UUID IDs (e.g., new system)
# -----------------------------
class TestPersonWithUuidId:
    def test_lifecycle_with_uuid_id(self):
        person = Person(name="Charlie", age=45, email="charlie@example.com")
        assert person.is_tbd

        uid = uuid.uuid4()
        person.resolve_id(uid)

        assert not person.is_tbd
        assert person.id == uid
        assert isinstance(person.id, uuid.UUID)

    def test_validation_can_be_added_per_type(self):
        # Example: we could subclass for stricter validation if needed
        @dataclass
        class StrictUuidPerson(Person[uuid.UUID]):
            def _validate_id(self, value: uuid.UUID) -> None:
                if value.version != 4:
                    raise ValueError("Only v4 UUIDs allowed")

        p = StrictUuidPerson(name="Dave", age=50)
        p.resolve_id(uuid.uuid4())  # OK

        with pytest.raises(ValueError):
            p.resolve_id(uuid.uuid1())  # version 1 → rejected


# -----------------------------
# Tests with int IDs (e.g., auto-increment DB)
# -----------------------------
class TestPersonWithIntId:
    def test_lifecycle_with_int_id(self):
        person = Person(name="Eve", age=35)
        assert person.is_tbd

        person.resolve_id(42)  # int ID (e.g., from DB sequence)

        assert not person.is_tbd
        assert person.id == 42
        assert isinstance(person.id, int)

    def test_equality_and_hashing_with_int(self):
        p1 = Person(name="Frank", age=60)
        p2 = Person(name="Grace", age=55)

        p1.resolve_id(1001)
        p2.resolve_id(1001)

        assert p1 == p2
        assert len({p1, p2}) == 1  # same hash & equal

        p3 = Person(name="Heidi", age=28)
        p3.resolve_id(1002)
        assert p1 != p3


# -----------------------------
# TBD Equality Tests
# -----------------------------
class TestTBDEquality:
    """Test equality behavior for TBD objects."""

    def test_tbd_objects_not_equal_to_each_other(self):
        """Two different TBD objects are not equal."""
        p1 = Person(name="Alice", age=30)
        p2 = Person(name="Alice", age=30)

        assert p1.is_tbd
        assert p2.is_tbd
        assert p1 != p2

    def test_tbd_object_equals_itself(self):
        """A TBD object equals itself."""
        p = Person(name="Alice", age=30)
        assert p.is_tbd
        assert p == p

    def test_tbd_objects_have_different_hashes(self):
        """Two TBD objects have different hashes (based on identity)."""
        p1 = Person(name="Alice", age=30)
        p2 = Person(name="Alice", age=30)

        assert hash(p1) != hash(p2)
        assert hash(p1) == hash(p1)  # Consistent

    def test_tbd_and_resolved_never_equal(self):
        """A TBD object never equals a resolved object."""
        p1 = Person(name="Alice", age=30)
        p2 = Person(name="Alice", age=30)
        p2.resolve_id("PER-001")

        assert p1.is_tbd
        assert not p2.is_tbd
        assert p1 != p2


# -----------------------------
# Validation Tests
# -----------------------------
class TestValidation:
    """Test ID validation."""

    def test_cannot_resolve_with_none(self):
        """Cannot resolve TBD with None value."""
        p = Person(name="Bob", age=25)

        with pytest.raises(ValueError, match="ID cannot be None"):
            p.resolve_id(None)

    def test_cannot_access_tbd_id(self):
        """Accessing .id on a TBD object raises an error."""
        p = Person(name="Charlie", age=35)

        with pytest.raises(ValueError, match="not yet assigned"):
            _ = p.id

    def test_cannot_reassign_once_resolved(self):
        """Cannot reassign an ID once it's been resolved."""
        p = Person(name="Dave", age=40)
        p.resolve_id("PER-123")

        with pytest.raises(ValueError, match="already has ID"):
            p.resolve_id("PER-456")

    def test_custom_validation_in_subclass(self):
        """Custom validation can enforce the ID format."""
        @dataclass
        class StrictPerson(Person[str]):
            def _validate_id(self, value: str) -> None:
                if not value.startswith("PER-"):
                    raise ValueError("ID must start with 'PER-'")

        p = StrictPerson(name="Eve", age=40)

        with pytest.raises(ValueError, match="must start with 'PER-'"):
            p.resolve_id("INVALID-123")

        # Valid ID works
        p.resolve_id("PER-123")
        assert p.id == "PER-123"


# -----------------------------
# Cross-type Tests
# -----------------------------
class TestCrossTypeComparison:
    """Test behavior across different ID types."""

    def test_different_id_types_are_never_equal(self):
        str_person = Person(name="Same", age=99)
        str_person.resolve_id("XYZ")

        uuid_person = Person(name="Same", age=99)
        uuid_person.resolve_id(uuid.uuid4())

        int_person = Person(name="Same", age=99)
        int_person.resolve_id(123)

        assert str_person != uuid_person
        assert str_person != int_person
        assert uuid_person != int_person

    def test_same_type_parameter_different_instances(self):
        """Different instances of the same type are only equal if IDs match."""
        p1 = Person(name="Alice", age=30)
        p2 = Person(name="Bob", age=40)

        p1.resolve_id("PER-100")
        p2.resolve_id("PER-200")

        assert p1 != p2

        p3 = Person(name="Charlie", age=50)
        p3.resolve_id("PER-100")

        assert p1 == p3  # Same ID, same type


# -----------------------------
# Edge Cases
# -----------------------------
class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_can_use_in_sets(self):
        """Resolved objects can be used in sets."""
        p1 = Person(name="Alice", age=30)
        p2 = Person(name="Bob", age=40)
        p3 = Person(name="Charlie", age=50)

        p1.resolve_id("PER-001")
        p2.resolve_id("PER-002")
        p3.resolve_id("PER-001")  # Same ID as p1 instance

        person_set = {p1, p2, p3}
        assert len(person_set) == 2  # p1 and p3 are equal

    def test_can_use_in_dicts(self):
        """Resolved objects can be used as dict keys."""
        p1 = Person(name="Alice", age=30)
        p2 = Person(name="Bob", age=40)

        p1.resolve_id("PER-001")
        p2.resolve_id("PER-001")

        data = {p1: "first", p2: "second"}

        assert len(data) == 1  # p1 and p2 are the same key
        assert data[p1] == "second"

    def test_tbd_objects_cannot_be_used_in_sets_reliably(self):
        """TBD objects hash by identity, so multiple TBD objects in a set."""
        p1 = Person(name="Alice", age=30)
        p2 = Person(name="Alice", age=30)

        person_set = {p1, p2}
        assert len(person_set) == 2  # Different identities

    def test_id_property_after_resolution(self):
        """The .id property works correctly after resolution."""
        p = Person(name="Test", age=25)

        # Before resolution
        assert p.is_tbd
        with pytest.raises(ValueError):
            _ = p.id

        # After resolution
        p.resolve_id("PER-123")
        assert not p.is_tbd
        assert p.id == "PER-123"

        # Can access multiple times
        assert p.id == "PER-123"
        assert p.id == "PER-123"