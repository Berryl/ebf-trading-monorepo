import pytest

from src.ebf_domain.rules.rule import RuleViolation
from src.ebf_domain.rules.validation_result import ValidationResult


class TestValidationResult:
    """Tests for ValidationResult."""

    @pytest.fixture
    def errors(self) -> list[RuleViolation]:
        return [RuleViolation("email", "format", "non-profit"), RuleViolation("name", "blank", "value_me")]

    class TestFactoryMethods:

        def test_success(self):
            result = ValidationResult.success()

            assert result.is_valid is True
            assert result.violations == []

        def test_failure(self, errors: list[RuleViolation]):
            result = ValidationResult.failure(errors)

            assert result.is_valid is False
            assert len(result.violations) == 2

    class TestBoolConversion:

        def test_when_valid_result(self):
            result = ValidationResult.success()

            assert bool(result) is True
            assert result  # Can use directly in if statements

        def test_when_invalid_result(self, errors: list[RuleViolation]):
            result = ValidationResult.failure(errors)
            assert bool(result) is False
            assert not result

    class TestAdding:

        def test_add_single_violation(self, errors: list[RuleViolation]):
            sut = ValidationResult.success()
            assert sut.is_valid

            sut.add_violation(errors[0])

            assert not sut.is_valid
            assert len(sut.violations) == 1

        def test_add_violation_list(self, errors: list[RuleViolation]):
            result = ValidationResult.success()

            result.add_violations(errors)

            assert not result.is_valid
            assert len(result.violations) == 2

    class TestStringRepresentation:

        def test_when_success(self):
            result = ValidationResult.success()
            assert "passed" in str(result)

        def test_when_failure(self, errors: list[RuleViolation]):
            result = ValidationResult.failure(errors)

            assert str(result).startswith("Validation failed with 2 errors:")
            assert "email" in str(result)
            assert "name" in str(result)