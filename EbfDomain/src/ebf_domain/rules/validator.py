from dataclasses import dataclass, field
from typing import Any, Callable, Self

from src.ebf_domain.rules.rule import RuleViolation
from src.ebf_domain.rules.rule_collection import RuleCollection


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
        return f"Validation failed with {len(self.violations)} error(s):\n  {violation_lines}"

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


@dataclass
class Validator[T]:
    """
    Orchestrates validation across multiple fields of an object.
    
    A Validator maps field names to RuleCollections and can validate
    entire objects or individual fields.
    
    Type Parameters:
        T: The type of object this validator validates
    
    Usage:
        ```python
        # Define a validator for a User class
        user_validator = Validator[User]()
        user_validator.add_rules("username", RuleCollection.from_rules(
            RequiredRule(),
            MinLengthRule(min_length=3),
            MaxLengthRule(max_length=20)
        ))
        user_validator.add_rules("email", RuleCollection.from_rules(
            RequiredRule(),
            EmailRule()
        ))
        
        # Validate an object
        user = User(username="ab", email="invalid")
        result = user_validator.validate(user)
        if not result:
            print(result) # Shows all violations
        ```
    """
    field_rules: dict[str, RuleCollection] = field(default_factory=dict)

    def add_rules(self, field_name: str, rules: RuleCollection) -> Self:
        """
        Add a rule collection for a specific field.
        
        Args:
            field_name: Name of the field to validate
            rules: RuleCollection to apply to this field
            
        Returns:
            Self for method chaining
        """
        self.field_rules[field_name] = rules
        return self

    def validate_field(self, field_name: str, value: Any) -> ValidationResult:
        """
        Validate a single field value.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            
        Returns:
            ValidationResult with any violations found
        """
        if field_name not in self.field_rules:
            return ValidationResult.success()

        violations = self.field_rules[field_name].validate(field_name, value)
        if violations:
            return ValidationResult.failure(violations)
        return ValidationResult.success()

    def validate(self, obj: T, field_accessor: Callable[[T, str], Any] = None) -> ValidationResult:
        """
        Validate all fields of an object.
        
        Args:
            obj: The object to validate
            field_accessor: Optional function to extract field values.
                          Default: getattr(obj, field_name)
            
        Returns:
            ValidationResult with all violations found
        """
        if field_accessor is None:
            field_accessor = getattr

        result = ValidationResult.success()

        for field_name, rule_collection in self.field_rules.items():
            try:
                value = field_accessor(obj, field_name)
                violations = rule_collection.validate(field_name, value)
                result.add_violations(violations)
            except AttributeError:
                # Field doesn't exist on this object - skip it
                continue

        return result

    def validate_dict(self, data: dict[str, Any]) -> ValidationResult:
        """
        Validate a dictionary of field values.
        
        Args:
            data: Dictionary mapping field names to values
            
        Returns:
            ValidationResult with all violations found
        """
        result = ValidationResult.success()

        for field_name, rule_collection in self.field_rules.items():
            value = data.get(field_name)
            violations = rule_collection.validate(field_name, value)
            result.add_violations(violations)

        return result

    @classmethod
    def for_fields(cls, **field_rules: RuleCollection) -> Self:
        """
        Create a validator with field rules specified as kwargs.
        
        Args:
            **field_rules: Field names mapped to RuleCollections
            
        Returns:
            New Validator instance
            
        Usage:
            ```python
            validator = Validator.for_fields(
                username=RuleCollection.from_rules(RequiredRule(), MinLengthRule(3)),
                email=RuleCollection.from_rules(RequiredRule(), EmailRule())
            )
            ```
        """
        return cls(field_rules=dict(field_rules))
