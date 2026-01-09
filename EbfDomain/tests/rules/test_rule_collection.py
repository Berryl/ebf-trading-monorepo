import pytest

from src.ebf_domain.rules import common_rules as cr
from src.ebf_domain.rules.rule_collection import RuleCollection


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

    def test_from_rules_class_method(self):
        """Can create collection from rules using class method."""
        collection = RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5),
            cr.MaxStrSizeRule(max_length=20)
        )

        assert len(collection) == 3

    def test_validate_with_no_violations(self):
        """validate() returns empty list when all rules pass."""
        collection = RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5)
        )

        violations = collection.validate("username", "alice123")
        assert violations == []

    def test_validate_with_single_violation(self):
        """validate() returns list with one violation."""
        collection = RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5)
        )

        violations = collection.validate("username", "bob")  # Too short
        assert len(violations) == 1
        assert "at least 5" in violations[0].message

    def test_validate_with_multiple_violations(self):
        """validate() returns all violations found."""
        collection = RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5),
            cr.MaxStrSizeRule(max_length=10)
        )

        violations = collection.validate("password", "")  # Empty - violates required AND min_length
        assert len(violations) == 2

    def test_is_valid_returns_true_when_all_pass(self):
        """is_valid() returns True when all rules pass."""
        collection = RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5)
        )

        assert collection.is_valid("field", "valid_value") is True

    def test_is_valid_returns_false_when_any_fail(self):
        """is_valid() returns False when any rule fails."""
        collection = RuleCollection.from_rules(
            cr.ValueRequiredRule(),
            cr.MinStrSizeRule(min_length=5)
        )

        assert collection.is_valid("field", "bad") is False

    def test_iterate_over_rules(self):
        """Can iterate over rules in collection."""
        rule1 = cr.ValueRequiredRule()
        rule2 = cr.MinStrSizeRule(min_length=5)
        collection = RuleCollection([rule1, rule2])

        rules_list = list(collection)
        assert len(rules_list) == 2
        assert rules_list[0] is rule1
        assert rules_list[1] is rule2
