from abc import ABC
from dataclasses import dataclass, KW_ONLY


@dataclass
class IDBase[T](ABC):
    """
    Base class for domain objects with IDs that may be assigned later.

    Supports the TBD (To-Be-Determined) pattern where objects are created
    without IDs and have them assigned during persistence or resolution.

    Type Parameters:
        T: The type of the ID (str, int, UUID, etc.)

    Note:
        Using KW_ONLY for id_value allows subclasses to define required fields
        without triggering "non-default field following default field" errors.

    Usage:
        Subclass IDBase with the ID type, then create objects in TBD
        state, and resolve their IDs later:
    ```python
            @dataclass(eq=False) # IMPORTANT to force subclasses to compare by ID
            class Trade(IDBase[str]):
                symbol: str
                quantity: int

            # Create without ID
            trade = Trade(symbol="GOLD", quantity=100)
            assert trade.is_tbd # True

            # Resolve the ID later
            trade.resolve_id("TR-001")
            assert trade.id == "TR-001" # Works
    ```

    If a class might require use with different ID types (as in a migration project), you can
    declare it generically once. When resolve_id is called, the type system will know what the ID type is:
    ``` python
            @dataclass(eq=False)
            class Person[T](IDBase[T]):
                name: str
                age: int

            # (e.g., legacy Excel system) using strs
            person = Person(name="Alice", age=30)
            person.resolve_id("PER-001") # it's a str!

            # (e.g., new system using ints)
            person = Person(name="Ted", age=18)
            person.resolve_id(17) # it's an int!
    ```
    """
    _: KW_ONLY
    id_value = None

    @property
    def is_tbd(self) -> bool:
        """Returns True if ID hasn't been assigned yet."""
        return self.id_value is None

    @property
    def id(self) -> T:
        """
        Get the ID value.

        Raises:
            ValueError: If ID is still in TBD state
        """
        if self.is_tbd:
            raise ValueError(f"{self.__class__.__name__} ID is not yet assigned (TBD state)")
        return self.id_value

    def resolve_id(self, value: T) -> None:
        """
        Assign an ID to an object in the TBD state.

        Args:
            value: The ID value to assign (must not be None)

        Raises:
            ValueError: If the object is not in TBD state (ID already assigned)
            ValueError: If value is None
        """
        if not self.is_tbd:
            raise ValueError(
                f"{self.__class__.__name__} already has ID '{self.id_value}' - "
                "cannot reassign (not in TBD state)"
            )

        if value is None:
            raise ValueError(f"{self.__class__.__name__} ID cannot be None")

        self._validate_id(value)
        self.id_value = value

    def _validate_id(self, value: T) -> None:
        """
        Optional validation hook for ID values.
        Override in subclasses to add custom validation.

        Args:
            value: The ID value to validate

        Raises:
            ValueError: If validation fails
        """
        pass

    def __eq__(self, other) -> bool:
        """
        Two objects are equal if they have the same type and ID.
        TBD objects are only equal to themselves.
        """
        if not isinstance(other, self.__class__):
            return False

        # TBD objects are only equal by identity
        if self.is_tbd or other.is_tbd:
            return self is other

        return self.id_value == other.id_value

    def __hash__(self) -> int:
        """
        Hash based on type and ID.
        TBD objects hash by identity.
        """
        if self.is_tbd:
            return id(self)
        return hash((self.__class__, self.id_value))
