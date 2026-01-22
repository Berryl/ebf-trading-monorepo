import pytest

from ebf_domain.rules import common_rules as cr
from ebf_domain.rules.rule import Rule
from ebf_domain.rules.rule_collection import RuleCollection


class TestRuleCollection:
    """Tests for RuleCollection."""
    class TestAdd:
        @pytest.fixture
        def sut(self):
            return RuleCollection()

        def test_single_rule(self, sut):
            assert len(sut) == 0
            sut.add(cr.ValueRequiredRule())
            sut.add(cr.MinStrSizeRule(min_length=5))
            sut.add(cr.MaxStrSizeRule(max_length=20))

            assert len(sut) == 3

        def test_chaining(self, sut):
            sut = RuleCollection()
            result = sut.add(cr.ValueRequiredRule()).add(cr.MinStrSizeRule(5))

            assert isinstance(result, RuleCollection)
            assert len(sut) == 2

        class TestFactoryCreate:

            def test_can_add_variable_number_of_args(self):
                sut = RuleCollection.from_rules(
                    cr.ValueRequiredRule(),
                    cr.MinStrSizeRule(min_length=5),
                    cr.MaxStrSizeRule(max_length=20))

                assert len(sut) == 3

    class TestValidation:

        @pytest.fixture
        def sut(self):
            return RuleCollection.from_rules(
                cr.ValueRequiredRule(),
                cr.MinStrSizeRule(min_length=5)
            )

        class TestValidate:

            def test_when_no_violations(self, sut):
                assert sut.validate("username", "alice123") == []

            def test_when_single_violation(self, sut):
                result = sut.validate("username", "bob")  # Too short
                assert len(result) == 1
                assert "at least 5" in str(result[0])

            def test_when_multiple_violations(self, sut):
                assert len(sut.validate("password", "")) == 2, "empty violates value required AND min_length"

        class TestIsValid:

            def test_true_when_all_pass(self, sut):
                assert sut.is_valid("field", "valid_value") is True

            def test_is_valid_returns_false_when_any_fail(self, sut):
                assert sut.is_valid("field", "") is False

        class TestIteration:
            def test_can_iterate(self, sut):
                for rule in list(sut):
                    assert isinstance(rule, Rule)


