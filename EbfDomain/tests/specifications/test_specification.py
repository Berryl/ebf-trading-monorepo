import pytest
from ebf_core.guards.guards import ContractError

from helpers.spec_helpers import (
    SampleItem,
    ItemStatus,
    IsActive,
    IsClosed,
    IsPending,
    ValueGreaterThan,
    NameStartsWith,
    HasTag,
    make_item,
)
from src.ebf_domain.specifications.specification import Specification, AndSpecification, OrSpecification, \
    NotSpecification


class TestSpecification:

    @pytest.fixture
    def active_item(self) -> SampleItem:
        return make_item(name="Active", value=100, status=ItemStatus.ACTIVE, tags=["important"])

    @pytest.fixture
    def closed_item(self) -> SampleItem:
        return make_item(name="Closed", value=50, status=ItemStatus.CLOSED, tags=["archived"])

    @pytest.fixture
    def pending_item(self) -> SampleItem:
        return make_item(name="Pending", value=25, status=ItemStatus.PENDING)

    class TestSimpleSpec:
        @pytest.fixture
        def sut(self) -> Specification:
            return IsActive()

        def test_when_criteria_met(self, sut, active_item):
            assert sut.is_satisfied_by(active_item) is True

        def test_when_criteria_not_met(self, sut, closed_item):
            assert sut.is_satisfied_by(closed_item) is False

        def test_constructor_params(self):
            sut = ValueGreaterThan(75)

            assert sut.is_satisfied_by(make_item(value=100)) is True
            assert sut.is_satisfied_by(make_item(value=50)) is False

        def test_repr(self, sut):
            assert repr(IsActive()) == "IsActive()"
            assert repr(ValueGreaterThan(100)) == "ValueGreaterThan(100)"

    class TestAndSpecification:

        @pytest.fixture
        def matches_both(self) -> SampleItem:
            return make_item(value=100, status=ItemStatus.ACTIVE)

        @pytest.fixture
        def matches_first_only(self) -> SampleItem:
            return make_item(value=25, status=ItemStatus.ACTIVE)

        @pytest.fixture
        def matches_second_only(self) -> SampleItem:
            return make_item(value=100, status=ItemStatus.CLOSED)

        @pytest.fixture
        def matches_neither(self) -> SampleItem:
            return make_item(value=25, status=ItemStatus.CLOSED)

        def test_satisfied_when_both_specs_match(self, matches_both):
            sut = AndSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_both) is True

        def test_not_satisfied_when_only_left_matches(self, matches_first_only):
            sut = AndSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_first_only) is False

        def test_not_satisfied_when_only_right_matches(self, matches_second_only):
            sut = AndSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_second_only) is False

        def test_not_satisfied_when_neither_matches(self, matches_neither):
            sut = AndSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_neither) is False

        def test_rejects_none_left_spec(self):
            with pytest.raises(ContractError, match="'left' cannot be None"):
                AndSpecification(None, IsActive())  # noqa

        def test_rejects_none_right_spec(self):
            with pytest.raises(ContractError, match="'right' cannot be None"):
                AndSpecification(IsActive(), None)  # noqa

    class TestOrSpecification:

        @pytest.fixture
        def matches_both(self) -> SampleItem:
            return make_item(value=100, status=ItemStatus.ACTIVE)

        @pytest.fixture
        def matches_first_only(self) -> SampleItem:
            return make_item(value=25, status=ItemStatus.ACTIVE)

        @pytest.fixture
        def matches_second_only(self) -> SampleItem:
            return make_item(value=100, status=ItemStatus.CLOSED)

        @pytest.fixture
        def matches_neither(self) -> SampleItem:
            return make_item(value=25, status=ItemStatus.CLOSED)

        def test_satisfied_when_both_specs_match(self, matches_both):
            sut = OrSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_both) is True

        def test_satisfied_when_only_left_matches(self, matches_first_only):
            sut = OrSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_first_only) is True

        def test_satisfied_when_only_right_matches(self, matches_second_only):
            sut = OrSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_second_only) is True

        def test_not_satisfied_when_neither_matches(self, matches_neither):
            sut = OrSpecification(IsActive(), ValueGreaterThan(75))

            assert sut.is_satisfied_by(matches_neither) is False

        def test_rejects_none_left_spec(self):
            with pytest.raises(ContractError, match="'left' cannot be None"):
                OrSpecification(None, IsActive())  # noqa

        def test_rejects_none_right_spec(self):
            with pytest.raises(ContractError, match="'right' cannot be None"):
                OrSpecification(IsActive(), None)  # noqa

    class TestNotSpecification:

        def test_satisfied_when_inner_spec_not_satisfied(self):
            sut = NotSpecification(IsActive())
            closed_item = make_item(status=ItemStatus.CLOSED)

            assert sut.is_satisfied_by(closed_item) is True

        def test_not_satisfied_when_inner_spec_satisfied(self):
            sut = NotSpecification(IsActive())
            active_item = make_item(status=ItemStatus.ACTIVE)

            assert sut.is_satisfied_by(active_item) is False

        def test_double_negation_equals_original(self):
            item = make_item(status=ItemStatus.ACTIVE)
            original = IsActive()

            double_negated = NotSpecification(NotSpecification(original))

            assert original.is_satisfied_by(item) == double_negated.is_satisfied_by(item)

        def test_rejects_none_spec(self):
            with pytest.raises(ContractError, match="'spec' cannot be None"):
                NotSpecification(None)  # noqa

    class TestOperatorOverloading:

        @pytest.fixture
        def item(self) -> SampleItem:
            return make_item(value=100, status=ItemStatus.ACTIVE, tags=["important"])

        class TestAndOperator:

            def test_and_operator_creates_and_specification(self):
                result = IsActive() & ValueGreaterThan(75)

                assert isinstance(result, AndSpecification)

            def test_and_operator_evaluates_correctly(self, item):
                sut = IsActive() & ValueGreaterThan(75)

                assert sut.is_satisfied_by(item) is True

            def test_and_also_method_equivalent_to_operator(self, item):
                using_method = IsActive().and_also(ValueGreaterThan(75))
                using_operator = IsActive() & ValueGreaterThan(75)

                assert using_method.is_satisfied_by(item) == using_operator.is_satisfied_by(item)

            def test_and_operator_rejects_none(self):
                with pytest.raises(ContractError, match="'other' cannot be None"):
                    IsActive() & None  # noqa

        class TestOrOperator:

            def test_or_operator_creates_or_specification(self):
                result = IsActive() | ValueGreaterThan(75)

                assert isinstance(result, OrSpecification)

            def test_or_operator_evaluates_correctly(self, item):
                sut = IsActive() | ValueGreaterThan(1000)

                assert sut.is_satisfied_by(item) is True

            def test_or_else_method_equivalent_to_operator(self, item):
                using_method = IsActive().or_else(ValueGreaterThan(75))
                using_operator = IsActive() | ValueGreaterThan(75)

                assert using_method.is_satisfied_by(item) == using_operator.is_satisfied_by(item)

            def test_or_operator_rejects_none(self):
                with pytest.raises(ContractError, match="'other' cannot be None"):
                    IsActive() | None  # noqa

        class TestNotOperator:

            def test_not_operator_creates_not_specification(self):
                result = ~IsActive()

                assert isinstance(result, NotSpecification)

            def test_not_operator_evaluates_correctly(self, item):
                sut = ~IsClosed()

                assert sut.is_satisfied_by(item) is True

            def test_negated_method_equivalent_to_operator(self, item):
                using_method = IsClosed().negated()
                using_operator = ~IsClosed()

                assert using_method.is_satisfied_by(item) == using_operator.is_satisfied_by(item)

    class TestComplexComposition:

        def test_chaining_multiple_and_conditions(self):
            item = make_item(name="ActiveHigh", value=100, status=ItemStatus.ACTIVE)

            sut = IsActive() & ValueGreaterThan(75) & NameStartsWith("Active")

            assert sut.is_satisfied_by(item) is True

        def test_chaining_multiple_or_conditions(self):
            item = make_item(value=50, status=ItemStatus.PENDING)

            sut = IsActive() | IsClosed() | ValueGreaterThan(1000)

            assert sut.is_satisfied_by(item) is False

        def test_combining_and_with_or(self):
            active_low = make_item(value=25, status=ItemStatus.ACTIVE)
            closed_high = make_item(value=100, status=ItemStatus.CLOSED)
            active_high = make_item(value=100, status=ItemStatus.ACTIVE)

            sut = (IsActive() | IsClosed()) & ValueGreaterThan(75)

            assert sut.is_satisfied_by(active_low) is False
            assert sut.is_satisfied_by(closed_high) is True
            assert sut.is_satisfied_by(active_high) is True

        def test_combining_or_with_and(self):
            active_high = make_item(value=100, status=ItemStatus.ACTIVE)
            closed_high = make_item(value=100, status=ItemStatus.CLOSED)
            active_low = make_item(value=25, status=ItemStatus.ACTIVE)

            sut = (IsActive() & ValueGreaterThan(75)) | IsClosed()

            assert sut.is_satisfied_by(active_high) is True
            assert sut.is_satisfied_by(closed_high) is True
            assert sut.is_satisfied_by(active_low) is False

        def test_negation_of_complex_expression(self):
            item = make_item(value=50, status=ItemStatus.ACTIVE)

            sut = ~(IsActive() & ValueGreaterThan(75))

            assert sut.is_satisfied_by(item) is True

        def test_de_morgans_law_not_and_equals_not_or_not(self):
            """NOT (A AND B) ≡ (NOT A) OR (NOT B)"""
            item = make_item(value=50, status=ItemStatus.ACTIVE)

            left_side = ~(IsActive() & ValueGreaterThan(75))
            right_side = (~IsActive()) | (~ValueGreaterThan(75))

            assert left_side.is_satisfied_by(item) == right_side.is_satisfied_by(item)

        def test_de_morgans_law_not_or_equals_not_and_not(self):
            """NOT (A OR B) ≡ (NOT A) AND (NOT B)"""
            item = make_item(value=50, status=ItemStatus.PENDING)

            left_side = ~(IsActive() | ValueGreaterThan(75))
            right_side = (~IsActive()) & (~ValueGreaterThan(75))

            assert left_side.is_satisfied_by(item) == right_side.is_satisfied_by(item)

        def test_complex_business_query(self):
            matching = make_item(
                name="ActiveItem",
                value=100,
                status=ItemStatus.ACTIVE,
                tags=["important", "urgent"],
            )

            not_matching_status = make_item(value=100, status=ItemStatus.CLOSED, tags=["important"])

            not_matching_value = make_item(value=25, status=ItemStatus.ACTIVE, tags=["important"])

            not_matching_tags = make_item(value=100, status=ItemStatus.ACTIVE, tags=["other"])

            sut = (IsActive() | IsPending()) & ValueGreaterThan(75) & (HasTag("important") | HasTag("urgent"))

            assert sut.is_satisfied_by(matching) is True
            assert sut.is_satisfied_by(not_matching_status) is False
            assert sut.is_satisfied_by(not_matching_value) is False
            assert sut.is_satisfied_by(not_matching_tags) is False

    class TestFiltering:

        @pytest.fixture
        def items(self) -> list[SampleItem]:
            return [
                make_item(name="Active1", value=100, status=ItemStatus.ACTIVE, tags=["important"]),
                make_item(name="Active2", value=50, status=ItemStatus.ACTIVE, tags=["normal"]),
                make_item(name="Closed1", value=100, status=ItemStatus.CLOSED, tags=["important"]),
                make_item(name="Closed2", value=25, status=ItemStatus.CLOSED, tags=["archived"]),
                make_item(name="Pending1", value=75, status=ItemStatus.PENDING, tags=["new"]),
            ]

        def test_single_spec(self, items):
            spec = IsActive()

            result = [item for item in items if spec.is_satisfied_by(item)]

            assert len(result) == 2
            assert all(item.status == ItemStatus.ACTIVE for item in result)

        def test_combined_specs(self, items):
            spec = IsActive() & ValueGreaterThan(75)

            result = [item for item in items if spec.is_satisfied_by(item)]

            assert len(result) == 1
            assert result[0].name == "Active1"

        def test_with_negation(self, items):
            spec = ~IsClosed()

            result = [item for item in items if spec.is_satisfied_by(item)]

            assert len(result) == 3
            assert all(item.status != ItemStatus.CLOSED for item in result)

        def test_complex_query(self, items):
            spec = (ValueGreaterThan(60) | HasTag("important")) & ~IsPending()

            result = [item for item in items if spec.is_satisfied_by(item)]

            expected_names = {"Active1", "Closed1"}
            actual_names = {item.name for item in result}
            assert actual_names == expected_names

        def test_when_none_match(self, items):
            spec = IsActive() & ValueGreaterThan(1000)

            result = [item for item in items if spec.is_satisfied_by(item)]

            assert len(result) == 0

        def test_when_all_match(self, items):
            spec = ValueGreaterThan(0)

            result = [item for item in items if spec.is_satisfied_by(item)]

            assert len(result) == len(items)


class TestSpecificationRepresentation:

    def test_and_spec_repr(self):
        sut = IsActive() & ValueGreaterThan(75)

        assert repr(sut) == "(IsActive() & ValueGreaterThan(75))"

    def test_or_spec_repr(self):
        sut = IsActive() | IsClosed()

        assert repr(sut) == "(IsActive() | IsClosed())"

    def test_not_spec_repr(self):
        sut = ~IsActive()

        assert repr(sut) == "~IsActive()"

    def test_complex_repr(self):
        sut = (IsActive() & ValueGreaterThan(75)) | IsClosed()

        expected = "((IsActive() & ValueGreaterThan(75)) | IsClosed())"
        assert repr(sut) == expected
