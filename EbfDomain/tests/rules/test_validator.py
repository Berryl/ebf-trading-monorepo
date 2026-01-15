from dataclasses import dataclass

import pytest

import ebf_domain.rules.common_rules as cr
from ebf_domain.rules.rule import Rule
from ebf_domain.rules.rule_collection import RuleCollection
from ebf_domain.rules.validation_result import ValidationResult
from ebf_domain.rules.validator import Validator


class TestValidator:
    """Tests for Validator."""

    @pytest.fixture(scope="class")
    def rules(self) -> RuleCollection:
        return RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5)
        )

    @dataclass
    class User:
        username: str
        email: str = None

    class TestAdding:

        @pytest.fixture(scope="class")
        def one_rule(self) -> Rule:
            return cr.EmailRule()

        @pytest.fixture
        def sut(self) -> Validator:
            return Validator()

        def test_can_add_a_rules_collection(self, sut, rules: RuleCollection):
            assert len(sut.field_rules) == 0

            sut.add("name", rules)

            assert len(sut.field_rules) == 1

        def test_can_add_a_single_rules(self, sut, one_rule: Rule):
            assert len(sut.field_rules) == 0

            sut.add("name", one_rule)

            assert len(sut.field_rules) == 1

        def test_chaining(self, sut, rules: RuleCollection, one_rule: Rule):
            """add_rules() returns self for method chaining."""
            result = sut.add("name", one_rule).add("age", rules)

            assert isinstance(result, Validator)
            assert len(sut.field_rules) == 2

            assert len(sut.field_rules["name"]) == 1
            assert len(sut.field_rules["age"]) == 2

    class TestValidating:

        @pytest.fixture
        def sut(self, rules) -> Validator:
            v = Validator()
            v.add("name", rules=rules)
            v.add("email", rules=RuleCollection.from_rules(cr.EmailRule()))
            return v

        @pytest.fixture(scope="class")
        def user_with_issues(self) -> "TestValidator.User":
            """ bad email AND bad username"""
            return TestValidator.User(username="ab", email="invalid")

        class TestFailurePolicy:
            def test_default_is_stop_on_first_failure(self, sut: Validator, user_with_issues):
                result: ValidationResult = sut.validate(user_with_issues)
                assert not result.is_valid
                assert len(result.violations) == 1

        class TestValidateDict:

            def test_with_valid_data(self, sut):
                data = {
                    "name": "alice",
                    "email": "alice@example.com"
                }
                assert sut.validate_dict(data).is_valid

            def test_with_invalid_data(self, sut):
                data = {
                    "name": "ab",  # Too short
                    "email": "invalid"  # Not an email
                }
                assert not sut.validate_dict(data).is_valid

            def test_missing_fields_makes_data_invalid(self, sut):
                """validate_dict() handles missing fields (treats as None)."""
                data = {}  # user is missing
                assert not sut.validate_dict(data).is_valid


        class TestValidateObject:

            def test_when_valid(self, sut):
                user = TestValidator.User(username="alice", email="alice@example.com")
                assert sut.validate(user).is_valid

            def test_when_invalid_data(self, sut):
                user = TestValidator.User(username="ab", email="not-email")
                assert not sut.validate(user).is_valid

            def test_when_missing_fields(self, sut):
                """validate() skips fields that don't exist on the object."""
                user = TestValidator.User(username="alice")
                # Should only validate username, skip email
                assert sut.validate(user).is_valid

        class TestValidateWithCustomAccessor:
            """validate() can use custom field accessor (Callable[[T, str], Any])."""

            def test_custom_field_accessor(self):

                @dataclass
                class User:
                    data: dict
                user = User(data={"user": "alice"})

                def dict_accessor_func(obj, field_name: str):
                    return obj.data.get(field_name)

                sut = Validator[User]()
                sut.add("user", RuleCollection.from_rules(cr.ValueRequiredRule()))

                result = sut.validate(user, field_accessor=dict_accessor_func)

                assert result.is_valid


    class TestFactoryCreate:

        def test_for_fields(self):
            sut = Validator.for_fields(
                username=RuleCollection.from_rules(cr.ValueRequiredRule(), cr.MinStrSizeRule(3)),
                email=RuleCollection.from_rules(cr.ValueRequiredRule(), cr.EmailRule())
            )

            assert len(sut.field_rules) == 2
            assert "username" in sut.field_rules
            assert "email" in sut.field_rules

    class TestScenarios:
        """Integration tests for complete validation scenarios."""

        class TestUserRegistration:

            @dataclass
            class UserRegistration:
                username: str
                email: str
                password: str
                age: int

            @pytest.fixture(scope="class")
            def sut(self) -> Validator:
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
                return validator

            def test_valid_registration(self, sut: Validator[UserRegistration]):
                valid_user = TestValidator.TestScenarios.TestUserRegistration.UserRegistration(
                    username="alice",
                    email="alice@example.com",
                    password="secure_password",
                    age=25
                )
                assert sut.validate(valid_user).is_valid

            def test_invalid_registration(self, sut: Validator[UserRegistration]):
                invalid_user = TestValidator.TestScenarios.TestUserRegistration.UserRegistration(
                    username="ab",  # Too short
                    email="invalid",  # Not an email
                    password="short",  # Too short
                    age=10  # Too young
                )
                assert sut.validate(invalid_user).is_valid is False

        class TestApiRequests:

            @pytest.fixture(scope="class")
            def sut(self) -> Validator:
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
                return validator

            def test_valid_api_request(self, sut: Validator):
                valid_request = {
                    "action": "create",
                    "resource_id": "RES-123"
                }
                assert sut.validate_dict(valid_request).is_valid

            def test_invalid_api_request(self, sut: Validator):
                invalid_request = {
                    "action": "invalid_action",
                    "resource_id": ""
                }

                result = sut.validate_dict(invalid_request)

                assert not result.is_valid
                assert len(result.violations) >= 2
