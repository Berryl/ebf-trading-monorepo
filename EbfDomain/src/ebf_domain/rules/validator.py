from dataclasses import dataclass, field
from enum import StrEnum, auto
from typing import Callable, Self, Any

from ebf_domain.rules.rule import Rule
from ebf_domain.rules.rule_collection import RuleCollection
from ebf_domain.rules.validation_result import ValidationResult


class FailureDisplayPolicy(StrEnum):
    SHOW_ALL_FAILURES = auto()
    STOP_ON_FIRST_FAIL = auto()


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

    def add(self, field_name: str, rules: RuleCollection | Rule[Any]) -> Self:
        """
        Add either a rule collection or a single rule for a specific field.
        
        Args:
            field_name: Name of the field to validate
            rules: RuleCollection or Rule to apply to this field
            
        Returns:
            Self for method chaining
        """
        if not isinstance(rules, RuleCollection):
            rules = RuleCollection.from_rules(rules)
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

    def validate(self, obj: T, field_accessor: Callable[[T, str], Any] = None,
                 policy: FailureDisplayPolicy = FailureDisplayPolicy.SHOW_ALL_FAILURES) -> ValidationResult:
        """
        Validate all fields of an object.
        
        Args:
            obj: The object to validate
            field_accessor: Optional function to extract field values.
                          Default: getattr(obj, field_name)
            policy: How to handle multiple failures. Default: SHOW_ALL_FAILURES
            
        Returns:
            ValidationResult with all violations found
        """
        if field_accessor is None:
            field_accessor = getattr

        result = ValidationResult.success()

        has_failures = False
        for field_name, rule_collection in self.field_rules.items():
            try:
                value = field_accessor(obj, field_name)
                violations = rule_collection.validate(field_name, value)
                result.add_violations(violations)
                has_failures = has_failures or len(violations) > 0

                if policy == FailureDisplayPolicy.STOP_ON_FIRST_FAIL and has_failures:
                    break
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
