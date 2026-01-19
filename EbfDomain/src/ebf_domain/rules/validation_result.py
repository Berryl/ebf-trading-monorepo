from dataclasses import dataclass, field
from typing import Self

from ebf_core.miscutil import string_helpers as sh

from ebf_domain.rules.rule import RuleViolation


@dataclass
class ValidationResult:
    """
    Result of a validation operation.

    Attributes:
        is_valid: True if validation passed, False otherwise
        violations: List of all rule violations found
    """
    is_valid: bool
    violations: list[RuleViolation] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Allow using ValidationResult in a boolean context."""
        return self.is_valid

    def __str__(self) -> str:
        if self.is_valid:
            return "Validation passed"

        violation_lines = "\n  ".join(str(v) for v in self.violations)
        error_desc = sh.pluralize_word(len(self.violations), "error", show_count=True)
        return f"Validation failed with {error_desc}:\n  {violation_lines}"

    def add_violation(self, violation: RuleViolation) -> None:
        """Add a violation to this result and mark as invalid."""
        self.violations.append(violation)
        self.is_valid = False

    def add_violations(self, violations: list[RuleViolation]) -> None:
        """Add multiple violations to this result."""
        if violations:
            self.violations.extend(violations)
            self.is_valid = False

    @classmethod
    def success(cls) -> Self:
        """Create a successful validation result."""
        return cls(is_valid=True)

    @classmethod
    def failure(cls, violations: list[RuleViolation]) -> Self:
        """Create a failed validation result with violations."""
        return cls(is_valid=False, violations=violations)
