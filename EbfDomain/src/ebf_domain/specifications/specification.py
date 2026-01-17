"""
Specification pattern for domain selection criteria.

Based on work by Eric Evans and Martin Fowler.
"""

from abc import ABC, abstractmethod
from typing import TypeVar

import ebf_core.guards.guards as g

T = TypeVar("T")


class Specification[T](ABC):
    """
    Base class for specifications that determine if an object matches criteria.

    Specifications represent selection criteria that can be combined using
    boolean logic (AND, OR, NOT) to build complex queries.

    Unlike Rules (which validate if something is allowed), Specifications
    query if something matches criteria - they have no notion of "valid" or
    "invalid", only "matches" or "doesn't match".

    Type Parameters:
        T: The type of object this specification evaluates

    Usage:
        ```python
        # Define concrete specifications
        class IsOpen(Specification[Trade]):
            def is_satisfied_by(self, trade: Trade) -> bool:
                return trade.status == TradeStatus.OPEN

        class IsWheel(Specification[Trade]):
            def is_satisfied_by(self, trade: Trade) -> bool:
                return trade.strategy_type == StrategyType.WHEEL

        # Combine using operators
        open_wheels = IsOpen() & IsWheel()
        closed_or_assigned = ~IsOpen() | HasAssignment()

        # Use for filtering
        matching = [t for t in trades if open_wheels.is_satisfied_by(t)]
        ```

    Composition:
        Specifications can be combined using Python operators:
        - `spec1 & spec2` - AND (both must match)
        - `spec1 | spec2` - OR (either must match)
        - `~spec` - NOT (must not match)

    Design Notes:
        - Specifications are stateless predicates (pure functions)
        - They should be immutable (no state changes after construction)
        - They represent domain concepts, not infrastructure queries
        - Use for in-memory filtering; adapt for database queries separately
    """

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool:
        """
        Determine if the candidate satisfies this specification.

        Args:
            candidate: The object to evaluate

        Returns:
            True if candidate matches this specification's criteria
        """
        raise NotImplementedError()

    def __and__(self, other: "Specification[T]") -> "Specification[T]":
        """
        Combine specifications with AND logic.

        Args:
            other: Specification to combine with

        Returns:
            New specification that requires both to be satisfied

        Example:
            ```python
            open_and_profitable = is_open & is_profitable
            ```
        """
        g.ensure_not_none(other, "other")
        return AndSpecification(self, other)

    def __or__(self, other: "Specification[T]") -> "Specification[T]":
        """
        Combine specifications with OR logic.

        Args:
            other: Specification to combine with

        Returns:
            New specification that requires either to be satisfied

        Example:
            ```python
            wheel_or_condor = is_wheel | is_condor
            ```
        """
        g.ensure_not_none(other, "other")
        return OrSpecification(self, other)

    def __invert__(self) -> "Specification[T]":
        """
        Negate this specification with NOT logic.

        Returns:
            New specification that matches when this one doesn't

        Example:
            ```python
            not_open = ~is_open
            ```
        """
        return NotSpecification(self)

    def and_also(self, other: "Specification[T]") -> "Specification[T]":
        """
        Explicit method for AND combination (alternative to & operator).

        Args:
            other: Specification to combine with

        Returns:
            New specification requiring both to be satisfied
        """
        return self & other

    def or_else(self, other: "Specification[T]") -> "Specification[T]":
        """
        Explicit method for OR combination (alternative to | operator).

        Args:
            other: Specification to combine with

        Returns:
            New specification requiring either to be satisfied
        """
        return self | other

    def negated(self) -> "Specification[T]":
        """
        Explicit method for NOT (alternative to ~ operator).

        Returns:
            New specification that matches when this one doesn't
        """
        return ~self


class AndSpecification[T](Specification[T]):
    """
    Specification that combines two specifications with AND logic.

    Both specifications must be satisfied for the combined specification
    to be satisfied.
    """

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Create AND specification.

        Args:
            left: First specification
            right: Second specification
        """
        g.ensure_not_none(left, "left")
        g.ensure_not_none(right, "right")
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies both specifications."""
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)

    def __repr__(self) -> str:
        return f"({self._left!r} & {self._right!r})"


class OrSpecification[T](Specification[T]):
    """
    Specification that combines two specifications with OR logic.

    Either specification can be satisfied for the combined specification
    to be satisfied.
    """

    def __init__(self, left: Specification[T], right: Specification[T]):
        """
        Create OR specification.

        Args:
            left: First specification
            right: Second specification
        """
        g.ensure_not_none(left, "left")
        g.ensure_not_none(right, "right")
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate satisfies either specification."""
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)

    def __repr__(self) -> str:
        return f"({self._left!r} | {self._right!r})"


class NotSpecification[T](Specification[T]):
    """
    Specification that negates another specification with NOT logic.

    The specification is satisfied when the wrapped specification is not satisfied.
    """

    def __init__(self, spec: Specification[T]):
        """
        Create NOT specification.

        Args:
            spec: Specification to negate
        """
        g.ensure_not_none(spec, "spec")
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        """Check if candidate does NOT satisfy the wrapped specification."""
        return not self._spec.is_satisfied_by(candidate)

    def __repr__(self) -> str:
        return f"~{self._spec!r}"