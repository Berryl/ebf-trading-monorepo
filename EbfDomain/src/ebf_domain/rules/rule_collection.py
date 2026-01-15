from dataclasses import dataclass, field
from typing import Self

from ebf_domain.rules.rule import Rule, RuleViolation


@dataclass
class RuleCollection[T]:
    """
    A collection of rules that can be applied to a value.
    
    RuleCollection allows you to group multiple rules together and
    validate a value against all of them, collecting any violations.
    If all rules pass, the result of validation will be None.
    
    Type Parameters:
        T: The type of value these rules validate
    
    Usage:
        ```python
        rules = RuleCollection([
            RequiredRule(),
            MinLengthRule(min_length=5),
            MaxLengthRule(max_length=50)
        ])
        
        result: list[RuleViolation] = rules.validate("username", "Bob")
        if result:
            print(f"Found {len(violations)} errors")
        ```
    """
    rules: list[Rule[T]] = field(default_factory=list)

    def add(self, rule: Rule[T]) -> Self:
        """
        Add a rule to this collection.
        
        Args:
            rule: The rule to add
            
        Returns:
            Self for method chaining
        """
        self.rules.append(rule)
        return self

    def validate(self, field_name: str, value: T) -> list[RuleViolation]:
        """
        Validate a value against all rules in this collection.
        
        Args:
            field_name: The name of the field being validated
            value: The value to validate
            
        Returns:
            List of violations (empty if all rules pass)
        """
        violations = []
        for rule in self.rules:
            violation = rule.validate(field_name, value)
            if violation is not None:
                violations.append(violation)
        return violations

    def is_valid(self, field_name: str, value: T) -> bool:
        """
        Check if a value passes all rules without returning violations.
        
        Args:
            field_name: The name of the field being validated
            value: The value to validate
            
        Returns:
            True if all rules pass, False otherwise
        """
        return len(self.validate(field_name, value)) == 0

    def __len__(self) -> int:
        """Return the number of rules in this collection."""
        return len(self.rules)

    def __iter__(self):
        """Iterate over the rules in this collection."""
        return iter(self.rules)

    @classmethod
    def from_rules(cls, *rules: Rule[T]) -> Self:
        """
        Create a RuleCollection from individual rules.
        
        Args:
            *rules: Variable number of rules
            
        Returns:
            New RuleCollection containing the rules
        """
        return cls(list(rules))
