from dataclasses import dataclass, FrozenInstanceError

import pytest

from src.ebf_domain.rules.rule import Rule, RuleViolation


# Test helper: A simple concrete rule implementation
@dataclass
class AlwaysFailRule(Rule[str]):
    """Test rule that always fails."""
    custom_message: str = "always fails"

    def validate(self, field_name: str, value: str) -> RuleViolation | None:
        return RuleViolation(
            field_name=field_name,
            message=self.custom_message,
            rule_name="always_fail",
            actual_value=value
        )


@dataclass
class AlwaysPassRule(Rule[str]):
    """Test rule that always passes."""

    def validate(self, field_name: str, value: str) -> RuleViolation | None:
        return None


class TestRuleViolation:
    """Tests for RuleViolation dataclass."""

    class TestInit:
        """Tests for RuleViolation creation."""

        def test_init_with_all_fields(self):
            """Can create rv with all fields."""
            rv = RuleViolation("email", "is not commercial", "nonprofit_domain", "ted@hotmail.com")

            assert rv.field_name == "email"
            assert rv.message == "is not commercial"
            assert rv.rule_name == "nonprofit_domain"
            assert rv.actual_value == "ted@hotmail.com"

        def test_actual_value_can_be_omitted(self):
            """Can create violation without actual_value."""
            rv = RuleViolation("password", "is required", "required")

            assert rv.actual_value is None

    class TestStringRepresentation:

        def test_when_actual_value_provided(self):
            """String representation includes actual value."""
            rv = RuleViolation(field_name="age", message="must be positive", rule_name="range", actual_value=-5)

            assert str(rv) == "age: must be positive (got: -5)"

        def test_when_actual_value_omitted(self):
            """String representation works without actual value."""
            rv = RuleViolation(field_name="username", message="is required", rule_name="required")

            assert str(rv) == "username: is required"

    class TestImmutability:

        def test_changes_raise_error(self):
            rv = RuleViolation(field_name="username", message="is required", rule_name="required")

            with pytest.raises(FrozenInstanceError):
                # noinspection PyDataclass
                rv.field_name = "changed"


class TestRuleBase:
    """Tests for Rule base class."""

    class TestValidation:

        def test_failure_returns_violation(self):
            rule = AlwaysFailRule(custom_message="test failure")

            result = rule.validate("field", "value")
            assert isinstance(result, RuleViolation)

        def test_success_returns_none(self):
            rule = AlwaysPassRule()

            result = rule.validate("field", "value")
            assert result is None

    class TestRuleName:

        # noinspection SpellCheckingInspection
        def test_rule_name_defaults_to_class_name(self):
            assert AlwaysFailRule().rule_name == "alwaysfail"

            assert AlwaysPassRule().rule_name == "alwayspass"

        def test_rule_name_can_be_defined_in_subclass(self):
            @dataclass
            class CustomNameRule(Rule[str]):
                @property
                def rule_name(self) -> str:
                    return "my_custom_rule"

                def validate(self, field_name: str, value: str) -> RuleViolation | None:
                    return None

            assert CustomNameRule().rule_name == "my_custom_rule"

    def test_instance_reusability(self):
        r = AlwaysFailRule(custom_message="same instance is reusable")

        v1 = r.validate("age", 32)
        v2 = r.validate("quantity", 100)

        assert v1.field_name == "age"
        assert v2.field_name == "quantity"
        assert v1.message == v2.message == "same instance is reusable"

    class TestGenerics:
        """Tests demonstrating generic type parameter usage."""

        def test_with_int(self):
            """Rule can be typed for integers."""

            @dataclass
            class PositiveRule(Rule[int]):
                def validate(self, field_name: str, value: int) -> RuleViolation | None:
                    if value is not None and value <= 0:
                        return RuleViolation(
                            field_name=field_name,
                            message="must be positive",
                            rule_name="positive",
                            actual_value=value
                        )
                    return None

            rule = PositiveRule()
            assert rule.validate("count", 5) is None
            assert rule.validate("count", -1) is not None

        def test_with_custom_type(self):
            """Rule can be typed for custom classes."""

            @dataclass
            class User:
                name: str
                age: int

            @dataclass
            class AdultUserRule(Rule[User]):
                def validate(self, field_name: str, value: User) -> RuleViolation | None:
                    if value is not None and value.age < 18:
                        return RuleViolation(
                            field_name=field_name,
                            message="must be 18 or older",
                            rule_name="adult",
                            actual_value=value
                        )
                    return None

            rule = AdultUserRule()
            adult = User(name="Alice", age=25)
            minor = User(name="Bob", age=15)

            assert rule.validate("user", adult) is None
            assert rule.validate("user", minor) is not None
