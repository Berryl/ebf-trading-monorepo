from src.ebf_domain.rules.rule import RuleViolation
from src.ebf_domain.rules.validation_result import ValidationResult


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_create_successful_result(self):
        """Can create a successful validation result."""
        result = ValidationResult.success()

        assert result.is_valid is True
        assert result.violations == []

    def test_create_failed_result(self):
        """Can create a failed validation result."""
        violations = [
            RuleViolation("field", "error", "rule")
        ]
        result = ValidationResult.failure(violations)

        assert result.is_valid is False
        assert len(result.violations) == 1

    def test_bool_conversion_for_valid_result(self):
        """ValidationResult can be used in boolean context - valid is True."""
        result = ValidationResult.success()
        assert bool(result) is True
        assert result  # Can use directly in if statements

    def test_bool_conversion_for_invalid_result(self):
        """ValidationResult can be used in boolean context - invalid is False."""
        result = ValidationResult.failure([
            RuleViolation("field", "error", "rule")
        ])
        assert bool(result) is False
        assert not result

    def test_add_violation(self):
        """Can add a violation to a result."""
        result = ValidationResult.success()
        assert result.is_valid

        result.add_violation(RuleViolation("field", "error", "rule"))

        assert not result.is_valid
        assert len(result.violations) == 1

    def test_add_violations(self):
        """Can add multiple violations to a result."""
        result = ValidationResult.success()

        violations = [
            RuleViolation("field1", "error1", "rule1"),
            RuleViolation("field2", "error2", "rule2")
        ]
        result.add_violations(violations)

        assert not result.is_valid
        assert len(result.violations) == 2

    def test_string_representation_for_success(self):
        """String representation for successful validation."""
        result = ValidationResult.success()
        assert "passed" in str(result).lower()

    def test_string_representation_for_failure(self):
        """String representation for failed validation."""
        violations = [
            RuleViolation("email", "is required", "required"),
            RuleViolation("password", "too short", "min_length")
        ]
        result = ValidationResult.failure(violations)

        str_result = str(result)
        assert "failed" in str_result.lower()
        assert "2 error" in str_result.lower()
        assert "email" in str_result
        assert "password" in str_result
