import re
from dataclasses import dataclass
from typing import Callable, Any

from src.ebf_domain.rules.rule import Rule, RuleViolation


@dataclass
class ValueRequiredRule(Rule[Any]):
    """
    Rule that checks if a value is not None or empty.
    
    Usage:
        ```python
        rule = RequiredRule()
        violation = rule.validate("email", None)  # Returns violation
        violation = rule.validate("email", "")    # Returns violation
        violation = rule.validate("email", "a@b.com")  # Returns None
        ```
    """
    
    def validate(self, field_name: str, value: Any) -> RuleViolation | None:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return RuleViolation(
                field_name=field_name,
                message="is required",
                rule_name="required",
                actual_value=value
            )
        return None


@dataclass
class RegexRule(Rule[str]):
    """
    Rule that validates a string against a regular expression pattern.
    
    Attributes:
        pattern: Regex pattern (as string or compiled Pattern)
        message: Custom error message (default: "does not match required format")
    
    Usage:
        ```python
        email_rule = RegexRule(
            pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$',
            message="must be a valid email address"
        )
        violation = email_rule.validate("email", "invalid")  # Returns violation
        ```
    """
    pattern: str | re.Pattern
    message: str = "does not match required format"
    
    def __post_init__(self):
        if isinstance(self.pattern, str):
            self.pattern = re.compile(self.pattern)
    
    def validate(self, field_name: str, value: str) -> RuleViolation | None:
        if value is None:
            return None  # Use RequiredRule for null checks
        
        if not self.pattern.match(value):
            return RuleViolation(
                field_name=field_name,
                message=self.message,
                rule_name="regex",
                actual_value=value
            )
        return None


@dataclass
class MinLengthRule(Rule[str]):
    """
    Rule that validates minimum string length.
    
    Usage:
        ```python
        rule = MinLengthRule(min_length=5)
        violation = rule.validate("password", "1234")  # Returns violation
        ```
    """
    min_length: int
    
    def validate(self, field_name: str, value: str) -> RuleViolation | None:
        if value is None:
            return None  # Use RequiredRule for null checks
        
        if len(value) < self.min_length:
            return RuleViolation(
                field_name=field_name,
                message=f"must be at least {self.min_length} characters",
                rule_name="min_length",
                actual_value=value
            )
        return None


@dataclass
class MaxLengthRule(Rule[str]):
    """
    Rule that validates maximum string length.
    
    Usage:
        ```python
        rule = MaxLengthRule(max_length=100)
        violation = rule.validate("bio", "x" * 101)  # Returns violation
        ```
    """
    max_length: int
    
    def validate(self, field_name: str, value: str) -> RuleViolation | None:
        if value is None:
            return None  # Use RequiredRule for null checks
        
        if len(value) > self.max_length:
            return RuleViolation(
                field_name=field_name,
                message=f"must be at most {self.max_length} characters",
                rule_name="max_length",
                actual_value=value
            )
        return None


@dataclass
class RangeRule(Rule[int | float]):
    """
    Rule that validates a numeric value is within a range.
    
    Attributes:
        min_value: Minimum allowed value (inclusive, None for no minimum)
        max_value: Maximum allowed value (inclusive, None for no maximum)
    
    Usage:
        ```python
        age_rule = RangeRule(min_value=0, max_value=150)
        violation = age_rule.validate("age", -5)  # Returns violation
        ```
    """
    min_value: int | float | None = None
    max_value: int | float | None = None
    
    def validate(self, field_name: str, value: int | float) -> RuleViolation | None:
        if value is None:
            return None  # Use RequiredRule for null checks
        
        if self.min_value is not None and value < self.min_value:
            return RuleViolation(
                field_name=field_name,
                message=f"must be at least {self.min_value}",
                rule_name="min_value",
                actual_value=value
            )
        
        if self.max_value is not None and value > self.max_value:
            return RuleViolation(
                field_name=field_name,
                message=f"must be at most {self.max_value}",
                rule_name="max_value",
                actual_value=value
            )
        
        return None


@dataclass
class CallableRule(Rule[Any]):
    """
    Rule that uses a custom callable function for validation.
    
    The callable should return True if validation passes, False otherwise.
    
    Attributes:
        validation_func: Function that takes a value and returns bool
        message: Error message when validation fails
    
    Usage:
        ```python
        def is_even(value: int) -> bool:
            return value % 2 == 0
        
        rule = CallableRule(
            validation_func=is_even,
            message="must be an even number"
        )
        violation = rule.validate("count", 3)  # Returns violation
        ```
    """
    validation_func: Callable[[Any], bool]
    message: str
    
    def validate(self, field_name: str, value: Any) -> RuleViolation | None:
        if value is None:
            return None  # Use RequiredRule for null checks
        
        try:
            is_valid = self.validation_func(value)
            if not is_valid:
                return RuleViolation(
                    field_name=field_name,
                    message=self.message,
                    rule_name="callable",
                    actual_value=value
                )
        except Exception as e:
            return RuleViolation(
                field_name=field_name,
                message=f"{self.message} (validation error: {e})",
                rule_name="callable",
                actual_value=value
            )
        
        return None


@dataclass
class EmailRule(Rule[str]):
    """
    Rule that validates email addresses.
    
    Uses a simplified but practical regex pattern for email validation.
    
    Usage:
        ```python
        rule = EmailRule()
        violation = rule.validate("email", "not-an-email")  # Returns violation
        violation = rule.validate("email", "user@example.com")  # Returns None
        ```
    """
    
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    def validate(self, field_name: str, value: str) -> RuleViolation | None:
        if value is None:
            return None  # Use RequiredRule for null checks
        
        if not self.EMAIL_PATTERN.match(value):
            return RuleViolation(
                field_name=field_name,
                message="must be a valid email address",
                rule_name="email",
                actual_value=value
            )
        return None


@dataclass
class OneOfRule(Rule[Any]):
    """
    Rule that validates a value is one of a set of allowed values.
    
    Attributes:
        allowed_values: Set of allowed values
        case_sensitive: For strings, whether comparison is case-sensitive (default: True)
    
    Usage:
        ```python
        rule = OneOfRule(allowed_values={"pending", "approved", "rejected"})
        violation = rule.validate("status", "unknown")  # Returns violation
        ```
    """
    allowed_values: set[Any]
    case_sensitive: bool = True
    
    def validate(self, field_name: str, value: Any) -> RuleViolation | None:
        if value is None:
            return None  # Use RequiredRule for null checks
        
        check_value = value
        allowed = self.allowed_values
        
        if not self.case_sensitive and isinstance(value, str):
            check_value = value.lower()
            allowed = {v.lower() if isinstance(v, str) else v for v in self.allowed_values}
        
        if check_value not in allowed:
            allowed_str = ", ".join(repr(v) for v in sorted(self.allowed_values, key=str))
            return RuleViolation(
                field_name=field_name,
                message=f"must be one of: {allowed_str}",
                rule_name="one_of",
                actual_value=value
            )
        return None
