from dataclasses import dataclass

import pytest

import src.ebf_domain.rules.common_rules as cr
from src.ebf_domain.rules.rule_collection import RuleCollection
from src.ebf_domain.rules.validator import Validator


class TestValidator:
    """Tests for Validator."""

    @pytest.fixture(scope="class")
    def rules(self) -> RuleCollection:
        return RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5)
        )

    class TestAdding:

        def test_field_rules_are_added(self, rules: RuleCollection):
            """Can add rules for a specific field."""
            validator = Validator()
            assert len(validator.field_rules) == 0

            validator.add_rules("name", rules)

            assert len(validator.field_rules) == 1

        def test_chaining(self, rules: RuleCollection):
            """add_rules() returns self for method chaining."""
            validator = Validator()

            result = validator.add_rules("name", cr.ValueRequiredRule()).add_rules("age", cr.ValueRequiredRule())
            assert result is validator
            assert len(validator.field_rules) == 2

    class TestValidating:

        @pytest.fixture
        def sut(self, rules) -> Validator:
            v = Validator()
            v.add_rules("name", rules=rules)
            v.add_rules("email", rules=RuleCollection.from_rules(cr.EmailRule()))
            return v

        class TestValidateField:

            def test_with_valid_value(self, sut):
                assert sut.validate_field("name", "Herbert").is_valid

            def test_with_invalid_value(self, sut):
                assert not sut.validate_field("name", "").is_valid

            def test_is_valid_when_field_not_in_validator(self, sut):
                assert sut.validate_field("unknown_field", "any_value").is_valid

        class TestValidateDictAndObject:
            @pytest.fixture
            def data(self) -> dict:
                return  {
                    "name": "alice",
                    "email": "alice@example.com"
                }

            def test_with_valid_data(self, sut, data):
                assert sut.validate_dict(data).is_valid

        def test_validate_dict_with_invalid_data(self):
            """validate_dict() finds violations in dictionary."""
            validator = Validator()
            validator.add_rules("username", RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.MinStrSizeRule(min_length=3)
            ))
            validator.add_rules("email", RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.EmailRule()
            ))

            data = {
                "username": "ab",  # Too short
                "email": "invalid"  # Not an email
            }
            result = validator.validate_dict(data)

            assert not result.is_valid
            assert len(result.violations) == 2

        def test_validate_dict_with_missing_fields(self):
            """validate_dict() handles missing fields (treats as None)."""
            validator = Validator()
            validator.add_rules("username", RuleCollection.from_rules(cr.ValueRequiredRule()))

            data = {}  # username is missing
            result = validator.validate_dict(data)

            assert not result.is_valid
            assert len(result.violations) == 1

        def test_validate_object_with_valid_data(self):
            """validate() validates an object successfully."""

            @dataclass
            class User:
                username: str
                email: str

            validator = Validator[User]()
            validator.add_rules("username", RuleCollection.from_rules(cr.ValueRequiredRule()))
            validator.add_rules("email", RuleCollection.from_rules(cr.EmailRule()))

            user = User(username="alice", email="alice@example.com")
            result = validator.validate(user)

            assert result.is_valid

        def test_validate_object_with_invalid_data(self):
            """validate() finds violations in object."""

            @dataclass
            class User:
                username: str
                email: str

            validator = Validator[User]()
            validator.add_rules("username", RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.MinStrSizeRule(min_length=3)
            ))
            validator.add_rules("email", RuleCollection.from_rules(cr.EmailRule()))

            user = User(username="ab", email="not-email")
            result = validator.validate(user)

            assert not result.is_valid
            assert len(result.violations) == 2

        def test_validate_object_with_missing_fields(self):
            """validate() skips fields that don't exist on object."""

            @dataclass
            class User:
                username: str

            validator = Validator[User]()
            validator.add_rules("username", RuleCollection.from_rules(cr.ValueRequiredRule()))
            validator.add_rules("email", RuleCollection.from_rules(cr.ValueRequiredRule()))  # email doesn't exist

            user = User(username="alice")
            result = validator.validate(user)

            # Should only validate username, skip email
            assert result.is_valid

    def test_for_fields_class_method(self):
        """Can create validator using for_fields() class method."""
        validator = Validator.for_fields(
            username=RuleCollection.from_rules(cr.ValueRequiredRule(), cr.MinStrSizeRule(3)),
            email=RuleCollection.from_rules(cr.ValueRequiredRule(), cr.EmailRule())
        )

        assert len(validator.field_rules) == 2
        assert "username" in validator.field_rules
        assert "email" in validator.field_rules

    def test_custom_field_accessor(self):
        """validate() can use custom field accessor."""

        @dataclass
        class User:
            data: dict

        def dict_accessor(obj: User, field_name: str):
            return obj.data.get(field_name)

        validator = Validator[User]()
        validator.add_rules("username", RuleCollection.from_rules(cr.ValueRequiredRule()))

        user = User(data={"username": "alice"})
        result = validator.validate(user, field_accessor=dict_accessor)

        assert result.is_valid


class TestValidatorIntegration:
    """Integration tests for complete validation scenarios."""

    def test_user_registration_validation(self):
        """Complete user registration validation scenario."""

        @dataclass
        class UserRegistration:
            username: str
            email: str
            password: str
            age: int

        validator = Validator.for_fields(
            username=RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.MinStrSizeRule(min_length=3),
                cr.MaxStrSizeRule(max_length=20)
            ),
            email=RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.EmailRule()
            ),
            password=RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.MinStrSizeRule(min_length=8)
            ),
            age=RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.NumericRangeRule(min_value=13, max_value=120)
            )
        )

        # Valid registration
        valid_user = UserRegistration(
            username="alice",
            email="alice@example.com",
            password="secure_password",
            age=25
        )
        result = validator.validate(valid_user)
        assert result.is_valid

        # Invalid registration
        invalid_user = UserRegistration(
            username="ab",  # Too short
            email="invalid",  # Not an email
            password="short",  # Too short
            age=10  # Too young
        )
        result = validator.validate(invalid_user)
        assert not result.is_valid
        assert len(result.violations) == 4

    def test_api_request_validation(self):
        """Validate API request data as dictionary."""
        validator = Validator.for_fields(
            action=RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.OneOfRule({"create", "update", "delete"})
            ),
            resource_id=RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.MinStrSizeRule(min_length=1)
            )
        )

        # Valid request
        valid_request = {
            "action": "create",
            "resource_id": "RES-123"
        }
        result = validator.validate_dict(valid_request)
        assert result.is_valid

        # Invalid request
        invalid_request = {
            "action": "invalid_action",
            "resource_id": ""
        }
        result = validator.validate_dict(invalid_request)
        assert not result.is_valid
        assert len(result.violations) >= 2
