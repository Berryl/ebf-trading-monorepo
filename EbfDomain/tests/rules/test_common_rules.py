import sys

import pytest

from ebf_domain.rules.common_rules import (
    ValueRequiredRule, RegexRule, MinStrSizeRule, MaxStrSizeRule,
    NumericRangeRule, CallableMustBeTrueRule, EmailRule, OneOfRule
)
from src.ebf_domain.rules.rule import Rule


class TestValueRequiredRule:
    """Tests for RequiredRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return ValueRequiredRule()

    @pytest.mark.parametrize("bad_value", [None, "", "   "])
    def test_fails_on_none_or_empty_str(self, sut, bad_value):
        result = sut.validate("password", bad_value)

        assert 'password: is required' in str(result)

    @pytest.mark.parametrize("good_value", ["hello", 12, False, [1, 2, 3], {}])
    def test_passes_on_any_value(self, sut, good_value):
        assert sut.validate("field", good_value) is None


class TestRegexRule:
    """Tests for RegexRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return RegexRule(r'^\d{3}-\d{4}$')

    @pytest.mark.parametrize("good_value", ["123-4567", "000-0000"])
    def test_matching_pattern_passes(self, sut, good_value):
        assert sut.validate("phone", good_value) is None

    def test_non_matching_pattern_fails(self, sut):
        result = sut.validate("phone", "blah")

        assert "phone: does not match required format" in str(result)

    def test_none_always_passes_on_none(self, sut):
        assert sut.validate("field", None) is None

    def test_can_use_compiled_pattern(self):
        import re
        rule = RegexRule(re.compile(r'^[A-Z]+$'))

        assert rule.validate("code", "ABC") is None
        assert rule.validate("code", "abc") is not None


class TestMinLengthRule:
    """Tests for MinLengthRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return MinStrSizeRule(min_length=3)

    @pytest.mark.parametrize("value", ["1", "12"])
    def test_below_minimum_length_fails(self, sut, value):
        result = sut.validate("password", "x")

        assert f'password: must be at least 3 characters' in str(result)

    @pytest.mark.parametrize("value", ["123", "1234678"])
    def test_at_or_above_minimum_length_passes(self, value):
        rule = MinStrSizeRule(min_length=3)
        assert rule.validate("field", value) is None

    def test_none__always_passes(self, sut):
        assert sut.validate("field", None) is None


class TestMaxLengthRule:
    """Tests for MaxLengthRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return MaxStrSizeRule(max_length=3)

    @pytest.mark.parametrize("value", ["1234", "123456"])
    def test_above_maximum_length_fails(self, sut, value):
        result = sut.validate("password", value)
        assert f'password: must be at most 3 characters' in str(result)

    @pytest.mark.parametrize("value", ["123", "2"])
    def test_at_or_below_maximum_length_passes(self, sut, value):
        assert sut.validate("field", value) is None

    def test_none_always_passes(self, sut):
        assert sut.validate("field", None) is None


class TestNumericRangeRule:
    """Tests for RangeRule."""

    @pytest.fixture
    def sut(self) -> Rule:
        return NumericRangeRule(min_value=0, max_value=100)

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
        sut.min_value = 0
        sut.max_value = None
        assert sut.validate("age", value) is None

    @pytest.mark.parametrize("value", [-.001, -50, -sys.maxsize, float('-inf')])
    def test_unspecified_minimum_is_negative_infinity(self, sut, value):
        sut.min_value = None
        sut.max_value = 100
        assert sut.validate("age", value) is None


class TestCallableRule:
    """Tests for CallableRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return CallableMustBeTrueRule(
            validation_func=lambda x: x % 2 == 0,
            message="must be even"
        )

    @pytest.mark.parametrize("good_value", [4, 16, 222])
    def test_true_eval_passes(self, sut, good_value):
        assert sut.validate("number", good_value) is None

    @pytest.mark.parametrize("bad_value", [9, -3, 27])
    def test_false_eval_fails(self, sut, bad_value):
        result = sut.validate("number", bad_value)

        assert 'number: must be even' in str(result)

    def test_exceptions_are_handled_with_useful_message(self):
        """CallableRule handles exceptions in validation function."""

        def buggy_validator(x):
            return x / 0  # Will raise ZeroDivisionError

        rule = CallableMustBeTrueRule(
            validation_func=buggy_validator,
            message="must pass validation"
        )
        result = rule.validate("field", 10)

        assert "(validation error: division by zero)" in str(result)

    def test_none__always_passes(self, sut):
        assert sut.validate("field", None) is None

    @pytest.mark.parametrize("good_value", ["user_123", "tom123"])
    @pytest.mark.parametrize("bad_value", ["123user", "tom@hotmail"])
    def test_can_use_arbitrarily_complex_validation_logic(self, good_value, bad_value):
        def is_valid_username(username: str) -> bool:
            if not username:
                return False
            if not username[0].isalpha():
                return False
            if not username.replace('_', '').isalnum():
                return False
            return True

        rule = CallableMustBeTrueRule(
            validation_func=is_valid_username,
            message="must start with letter and contain only letters, numbers, and underscores"
        )

        assert rule.validate("username", good_value) is None
        assert rule.validate("username", bad_value) is not None


class TestEmailRule:
    """Tests for EmailRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return EmailRule()

    @pytest.mark.parametrize("good_email", ["user@example.com", "tom@hotmail.org"])
    def test__valid_email_passes(self, sut, good_email):
        assert sut.validate("email", good_email) is None

    @pytest.mark.parametrize("bad_email", ["bob", "tom@hotmail"])
    def test__invalid_email_fails(self, sut, bad_email):
        result = sut.validate("email", bad_email)
        assert 'email: must be a valid email address' in str(result)

    def test_none_always_passes(self, sut):
        assert sut.validate("email", None) is None


class TestOneOfRule:
    """Tests for OneOfRule."""

    @pytest.fixture(scope="class")
    def sut(self) -> Rule:
        return OneOfRule(allowed_values={"red", "green", "blue"})

    @pytest.mark.parametrize("good_value", ["red", "blue", "green"])
    def test_value_is_in_set_passes(self, sut, good_value):
        assert sut.validate("color", good_value) is None

    @pytest.mark.parametrize("bad_value", ["X", "yellow", 1])
    def test_value_is_not_in_set_fails(self, sut, bad_value):
        result = sut.validate("color", bad_value)
        assert "color: must be one of: 'blue', 'green', 'red'" in str(result)

    @pytest.mark.parametrize("bad_value", ["RED", "bLUe", "GReeN"])
    def test_str_case_is_sensitive_by_default(self, sut, bad_value):
        result = sut.validate("color", bad_value)
        assert "color: must be one of: 'blue', 'green', 'red'" in str(result)

    def test_none_always_passes(self, sut):
        assert sut.validate("field", None) is None

    @pytest.mark.parametrize("good_value", ["RED", "bLUe", "GReeN"])
    def test_str_case_insensitivity_can_be_allowed(self, sut, good_value):
        sut.case_sensitive = False
        assert sut.validate("color", good_value) is None

    def test_case_sensitive_by_default(self):
        """OneOfRule is case-sensitive by default."""
        rule = OneOfRule(allowed_values={"RED", "GREEN", "BLUE"})

        assert rule.validate("color", "RED") is None
        assert rule.validate("color", "red") is not None

    @pytest.mark.parametrize("good_value", [1, 99, 3])
    def test_non_string_values_are_ok(self, sut, good_value):
        """OneOfRule works with non-string types."""
        sut.allowed_values = {1, 2, 3, 99}

        assert sut.validate("priority", good_value) is None


class TestRuleCombinations:
    """Tests for combining multiple rule types."""

    def test_combining_required_and_length_rules(self):
        """Can combine RequiredRule with length rules."""
        required = ValueRequiredRule()
        min_len = MinStrSizeRule(min_length=5)

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
        max_len = MaxStrSizeRule(max_length=10)

        # Both pass
        assert regex.validate("code", "12345") is None
        assert max_len.validate("code", "12345") is None

        # Regex fails, length passes
        assert regex.validate("code", "abc") is not None
        assert max_len.validate("code", "abc") is None

        # Both fail
        assert regex.validate("code", "12345678901") is None  # regex passes
        assert max_len.validate("code", "12345678901") is not None  # length fails
