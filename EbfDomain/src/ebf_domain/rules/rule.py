from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RuleViolation:
    """
    Represents a validation rule violation.
    
    Attributes:
        field_name: The name of the field that violated the rule
        message: Human-readable error message
        rule_name: The name of the rule that was violated
        actual_value: The value that caused the violation (optional)
    """
    field_name: str
    message: str
    rule_name: str
    actual_value: object = None

    def __str__(self) -> str:
        if self.actual_value is not None:
            return f"{self.field_name}: {self.message} (got: {self.actual_value!r})"
        return f"{self.field_name}: {self.message}"


@dataclass
class Rule[T](ABC):
    """
    Base class for validation rules.
    
    Rules are immutable, reusable validators that check a single constraint
    and return a RuleViolation if the constraint is not satisfied.
    
    Type Parameters:
        T: The type of value this rule validates
    
    Usage:
    ```python
        @dataclass
        class MinLengthRule(Rule[str]):
            min_length: int

            # noinspection GrazieInspection
            def validate(self, field_name: str, value: str) -> RuleViolation | None:
                if value is None or len(value) < self.min_length:

                    return RuleViolation(
                        field_name=field_name,
                        message=f"must be at least {self.min_length} characters",
                        rule_name="min_length",
                        actual_value=value
                    )
                return None
        
        # noinspection GrazieInspection
        rule = MinLengthRule(min_length=5)
        violation = rule.validate("username", "Bob") # Returns violation
    ```
    """

    @abstractmethod
    def validate(self, field_name: str, value: T) -> RuleViolation | None:
        """
        Validate a value against this rule.
        
        Args:
            field_name: The name of the field being validated (for error messages)
            value: The value to validate
            
        Returns:
            RuleViolation if the rule is violated, None if validation passes
        """
        pass

    @property
    def rule_name(self) -> str:
        """
        Get a readable name for this rule.
        Override in subclasses for custom naming.
        """
        return self.__class__.__name__.replace("Rule", "").lower()
