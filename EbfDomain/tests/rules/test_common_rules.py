import sys

import pytest

from src.ebf_domain.rules.common_rules import (
    ValueRequiredRule, RegexRule, MinLengthRule, MaxLengthRule,
    NumericRangeRule, CallableRule, EmailRule, OneOfRule
)
from src.ebf_domain.rules.rule import Rule


class TestValueRequiredRule:
    """Tests for RequiredRule."""

    @pytest.mark.parametrize("illegal_value", [None, "", "   "])
    def test_fails_on_none_or_empty_str(self, illegal_value):
        rule = ValueRequiredRule()
        v = rule.validate("password", illegal_value)

        assert 'password: is required' in str(v)

    @pytest.mark.parametrize("legal_value", ["hello", 12, False, [1, 2, 3], {}])
    def test_passes_on_any_value(self, legal_value):
        rule = ValueRequiredRule()

        assert rule.validate("field", legal_value) is None


class TestRegexRule:
    """Tests for RegexRule."""

    def test_matching_pattern_passes(self):
        rule = RegexRule(pattern=r'^\d{3}-\d{4}$')

        assert rule.validate("phone", "123-4567") is None

    def test_non_matching_pattern_fails(self):
        rule = RegexRule(pattern=r'^\d{3}-\d{4}$')
        violation = rule.validate("phone", "blah")

        assert violation is not None

    def test_can_use_compiled_pattern(self):
        import re
        pattern = re.compile(r'^[A-Z]+$')
        rule = RegexRule(pattern=pattern)

        assert rule.validate("code", "ABC") is None
        assert rule.validate("code", "abc") is not None

    def test_passes_on_none(self):
        """RegexRule passes on None (use ValueRequiredRule for null checks)."""
        rule = RegexRule(pattern=r'^\d+$')
        assert rule.validate("field", None) is None


class TestMinLengthRule:
    """Tests for MinLengthRule."""

    def test_below_minimum_length_fails(self):
        rule = MinLengthRule(min_length=5)
        v = rule.validate("password", "x")

        assert f'password: must be at least 5 characters' in str(v)

    @pytest.mark.parametrize("length", ["123", "1234678"])
    def test_minimum_or_exceeded_length_passes(self, length):
        rule = MinLengthRule(min_length=3)
        assert rule.validate("field", length) is None

    def test_none_passes(self):
        """MinLengthRule passes on None."""
        rule = MinLengthRule(min_length=5)
        assert rule.validate("field", None) is None


class TestMaxLengthRule:
    """Tests for MaxLengthRule."""

    def test_above_maximum_length_fails(self):
        rule = MaxLengthRule(max_length=3)
        v = rule.validate("password", "123456")

        assert f'password: must be at most 3 characters' in str(v)

    @pytest.mark.parametrize("length", ["123", "2"])
    def test_maximum_or_below_length_passes(self, length):
        rule = MaxLengthRule(max_length=3)
        assert rule.validate("field", length) is None

    def test_none_passes(self):
        """MaxLengthRule passes on None."""
        rule = MaxLengthRule(max_length=5)
        assert rule.validate("field", None) is None


class TestNumericRangeRule:
    """Tests for RangeRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return NumericRangeRule(min_value=0, max_value=100)

    # @pytest.mark.parametrize("value", [-1, -99])
    # def test_below_range_fails(self, value):
    #     rule = RangeRule(min_value=0, max_value=100)
    #     v = rule.validate("field", value) is None
    #

    @pytest.mark.parametrize("value", [1, 99, .01, 99.999])
    def test_value_within_range_passes(self, sut, value):
        assert sut.validate("age", value) is None

    @pytest.mark.parametrize("value", [100, 0])
    def test_value_at_range_boundary_passes(self, sut, value):
        assert sut.validate("age", value) is None

    @pytest.mark.parametrize("value", [-1, -0.0001])
    def test_value_below_minimum_fails(self, sut, value):
        result = sut.validate("age", value)
        assert "age: must be at least 0" in str(result)

    @pytest.mark.parametrize("value", [101, 100.0001])
    def test_value_above_maximum_fails(self, sut, value):
        result = sut.validate("age", value)
        assert "age: must be at most 100" in str(result)

    @pytest.mark.parametrize("value", [.001, 50, sys.maxsize, float('inf')])
    def test_unspecified_maximum_is_positive_infinity(self, sut, value):
        sut.max_value = None
        assert sut.validate("age", value) is None

    def test_min_only(self):
        """RangeRule works with only minimum specified."""
        rule = NumericRangeRule(min_value=0)

        assert rule.validate("count", 0) is None
        assert rule.validate("count", 1000) is None
        assert rule.validate("count", -1) is not None

    def test_max_only(self):
        """RangeRule works with only maximum specified."""
        rule = NumericRangeRule(max_value=100)

        assert rule.validate("score", 100) is None
        assert rule.validate("score", -1000) is None
        assert rule.validate("score", 101) is not None

    def test_works_with_floats(self):
        """RangeRule works with float values."""
        rule = NumericRangeRule(min_value=0.0, max_value=1.0)

        assert rule.validate("probability", 0.5) is None
        assert rule.validate("probability", -0.1) is not None
        assert rule.validate("probability", 1.1) is not None

    def test_passes_on_none(self):
        """RangeRule passes on None."""
        rule = NumericRangeRule(min_value=0, max_value=100)
        assert rule.validate("field", None) is None


class TestCallableRule:
    """Tests for CallableRule."""

    def test_passes_when_callable_returns_true(self):
        """CallableRule passes when validation function returns True."""
        rule = CallableRule(
            validation_func=lambda x: x % 2 == 0,
            message="must be even"
        )

        assert rule.validate("number", 4) is None
        assert rule.validate("number", 100) is None

    def test_fails_when_callable_returns_false(self):
        """CallableRule fails when validation function returns False."""
        rule = CallableRule(
            validation_func=lambda x: x % 2 == 0,
            message="must be even"
        )
        violation = rule.validate("number", 3)

        assert violation is not None
        assert violation.message == "must be even"

    def test_handles_exceptions_in_callable(self):
        """CallableRule handles exceptions in validation function."""

        def buggy_validator(x):
            return x / 0  # Will raise ZeroDivisionError

        rule = CallableRule(
            validation_func=buggy_validator,
            message="must pass validation"
        )
        violation = rule.validate("field", 10)

        assert violation is not None
        assert "validation error" in violation.message.lower()

    def test_passes_on_none(self):
        """CallableRule passes on None."""
        rule = CallableRule(
            validation_func=lambda x: len(x) > 0,
            message="must not be empty"
        )
        assert rule.validate("field", None) is None

    def test_can_use_complex_validation_logic(self):
        """CallableRule can encapsulate complex validation logic."""

        def is_valid_username(username: str) -> bool:
            # Complex multi-condition validation
            if not username:
                return False
            if not username[0].isalpha():
                return False
            if not username.replace('_', '').isalnum():
                return False
            return True

        rule = CallableRule(
            validation_func=is_valid_username,
            message="must start with letter and contain only letters, numbers, and underscores"
        )

        assert rule.validate("username", "user_123") is None
        assert rule.validate("username", "123user") is not None
        assert rule.validate("username", "user@name") is not None


class TestEmailRule:
    """Tests for EmailRule."""

    def test_passes_on_valid_emails(self):
        """EmailRule passes for valid email addresses."""
        rule = EmailRule()

        assert rule.validate("email", "user@example.com") is None
        assert rule.validate("email", "first.last@example.com") is None
        assert rule.validate("email", "user+tag@example.co.uk") is None
        assert rule.validate("email", "user_name@sub.example.com") is None

    def test_fails_on_invalid_emails(self):
        """EmailRule fails for invalid email addresses."""
        rule = EmailRule()

        assert rule.validate("email", "notanemail") is not None
        assert rule.validate("email", "@example.com") is not None
        assert rule.validate("email", "user@") is not None
        assert rule.validate("email", "user @example.com") is not None

    def test_passes_on_none(self):
        """EmailRule passes on None."""
        rule = EmailRule()
        assert rule.validate("email", None) is None


class TestOneOfRule:
    """Tests for OneOfRule."""

    def test_passes_when_value_in_set(self):
        """OneOfRule passes when value is in allowed set."""
        rule = OneOfRule(allowed_values={"red", "green", "blue"})

        assert rule.validate("color", "red") is None
        assert rule.validate("color", "green") is None
        assert rule.validate("color", "blue") is None

    def test_fails_when_value_not_in_set(self):
        """OneOfRule fails when value is not in allowed set."""
        rule = OneOfRule(allowed_values={"red", "green", "blue"})
        violation = rule.validate("color", "yellow")

        assert violation is not None
        assert "must be one of" in violation.message
        assert "red" in violation.message

    def test_case_sensitive_by_default(self):
        """OneOfRule is case-sensitive by default."""
        rule = OneOfRule(allowed_values={"RED", "GREEN", "BLUE"})

        assert rule.validate("color", "RED") is None
        assert rule.validate("color", "red") is not None

    def test_case_insensitive_when_specified(self):
        """OneOfRule can be case-insensitive."""
        rule = OneOfRule(
            allowed_values={"red", "green", "blue"},
            case_sensitive=False
        )

        assert rule.validate("color", "RED") is None
        assert rule.validate("color", "Red") is None
        assert rule.validate("color", "red") is None

    def test_works_with_non_string_values(self):
        """OneOfRule works with non-string values."""
        rule = OneOfRule(allowed_values={1, 2, 3})

        assert rule.validate("priority", 1) is None
        assert rule.validate("priority", 4) is not None

    def test_passes_on_none(self):
        """OneOfRule passes on None."""
        rule = OneOfRule(allowed_values={"a", "b", "c"})
        assert rule.validate("field", None) is None


class TestRuleCombinations:
    """Tests for combining multiple rule types."""

    def test_combining_required_and_length_rules(self):
        """Can combine RequiredRule with length rules."""
        required = ValueRequiredRule()
        min_len = MinLengthRule(min_length=5)

        # Both fail on empty
        assert required.validate("password", "") is not None
        assert min_len.validate("password", "") is not None

        # Required fails, min_len passes on None
        assert required.validate("password", None) is not None
        assert min_len.validate("password", None) is None

        # Both pass on valid value
        assert required.validate("password", "12345") is None
        assert min_len.validate("password", "12345") is None

    def test_combining_regex_and_length_rules(self):
        """Can combine RegexRule with length rules."""
        regex = RegexRule(pattern=r'^\d+$', message="must be numeric")
        max_len = MaxLengthRule(max_length=10)

        # Both pass
        assert regex.validate("code", "12345") is None
        assert max_len.validate("code", "12345") is None

        # Regex fails, length passes
        assert regex.validate("code", "abc") is not None
        assert max_len.validate("code", "abc") is None

        # Both fail
        assert regex.validate("code", "12345678901") is None  # regex passes
        assert max_len.validate("code", "12345678901") is not None  # length fails
