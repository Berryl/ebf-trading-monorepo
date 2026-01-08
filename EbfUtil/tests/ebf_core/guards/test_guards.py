import re
from pathlib import Path

import pytest

from ebf_core.guards.guards import ContractError


class TestEnsureType:

    def test_simple_type_when_valid(self):
        result = g.ensure_type(42, int, "valid_number")
        assert result == 42

    def test_complex_type_when_valid(self):
        value = [[1, 2], [3, 4]]
        result = g.ensure_type(value, list[list[int]], "matrix")
        assert result == value

    def test_simple_type_mismatch(self):
        msg = re.escape("Arg 'count' must be of type int (it was type str)")
        with pytest.raises(ContractError, match=msg):
            g.ensure_type("not a number", int, "count")

    def test_simple_type_mismatch_when_no_description(self):
        msg = re.escape("Value must be of type int (it was type str)")
        with pytest.raises(ContractError, match=msg):
            g.ensure_type("not a number", int)

    def test_parameter_of_none(self):
        msg = re.escape("Value must be of type int (it was type None)")
        with pytest.raises(ContractError, match=msg):
            g.ensure_type(None, int)

    def test_complex_type_mismatch(self):
        msg = re.escape("Arg 'numbers': item 0 of list is not an instance of int")
        with pytest.raises(ContractError, match=msg):
            g.ensure_type(["1", "2", "3"], list[int], "numbers")

    def test_complex_type_mismatch_when_no_description(self):
        msg = re.escape("Value: item 0 of list is not an instance of int")
        with pytest.raises(ContractError, match=msg):
            g.ensure_type(["1", "2", "3"], list[int])

    def test_nested_type_mismatch(self):
        msg = re.escape("Arg 'matrix': item 0 of item 0 of list is not an instance of int")
        with pytest.raises(ContractError, match=msg):
            g.ensure_type([["not", "numbers"]], list[list[int]], "matrix")

    def test_empty_list(self):
        assert g.ensure_type([], list[int], "empty_list") == []

    def test_custom_type(self):
        class Custom:
            pass

        obj = Custom()
        assert g.ensure_type(obj, Custom, "custom_object") == obj

    def test_none_in_list(self):
        msg = re.escape("Arg 'numbers': item 1 of list is not an instance of int")
        with pytest.raises(ContractError, match=msg):
            g.ensure_type([1, None, 3], list[int], "numbers")


class TestEnsureNotNone:

    def test_when_valid(self):
        g.ensure_not_none(42, "valid_number")
        pass  # No exception should be raised

    @pytest.mark.parametrize(
        "desc_param, msg",
        [
            ("valid_number", re.escape("Arg 'valid_number' cannot be None")),  # provided
            ("", re.escape("Value cannot be None")),  # not provided
        ])
    def test_description_parameter(self, desc_param, msg):
        with pytest.raises(ContractError, match=msg):
            g.ensure_not_none(None, desc_param)


class TestEnsureNotEmptyStr:

    def test_when_valid(self):
        g.ensure_not_empty_str('42', "filename")
        pass  # No exception should be raised

    @pytest.mark.parametrize(
        "value, desc_param, msg",
        [
            (None, "filename", re.escape("Arg 'filename' cannot be None")),  # provided
            ("      ", "filename", re.escape("Arg 'filename' cannot be an empty string")),  # provided
            ("", "", re.escape("Value cannot be an empty string")),  # not provided
        ])
    def test_description_parameter(self, value, desc_param, msg):
        with pytest.raises(ContractError, match=msg):
            g.ensure_not_empty_str(value, desc_param)


class TestEnsureAttribute:

    def test_when_attribute_exists(self):
        class Example:
            value = 42

        g.ensure_attribute(Example(), "value", "example_value")
        # No exception should be raised

    def test_when_attribute_does_not_exist_with_description(self):
        class Example:
            pass

        expected_msg = re.escape("example_value has no attribute 'missing_attr'")

        with pytest.raises(ContractError, match=expected_msg):
            g.ensure_attribute(Example(), "missing_attr", "example_value")

    def test_when_attribute_does_not_exist_without_description(self):
        class Example:
            pass

        expected_msg = re.escape("Example has no attribute 'missing_attr'")

        with pytest.raises(ContractError, match=expected_msg):
            g.ensure_attribute(Example(), "missing_attr")

    def test_when_attribute_is_none(self):
        class Example:
            value = None

        g.ensure_attribute(Example(), "value", "example_value")
        # No exception should be raised (presence is checked, not value)

    def test_when_candidate_is_none(self):
        msg = re.escape("Arg 'example_value' cannot be None")
        with pytest.raises(ContractError, match=msg):
            g.ensure_attribute(None, "missing_attr", "example_value")

class TestEnsureIn:

    def test_valid_with_list(self):
        g.ensure_in("yaml", ["yaml", "json", "toml"], "format")

    def test_valid_with_tuple(self):
        g.ensure_in(2, (1, 2, 3), "level")

    def test_valid_with_set(self):
        g.ensure_in("blue", {"red", "green", "blue"}, "color")

    def test_not_in_with_description(self):
        msg = re.escape("Arg 'mode' must be one of the allowed choices")
        with pytest.raises(ContractError, match=msg):
            g.ensure_in("dark", ["system", "light"], "mode")

    def test_not_in_without_description(self):
        msg = re.escape("Value must be one of the allowed choices")
        with pytest.raises(ContractError, match=msg):
            g.ensure_in("pdf", ["yaml", "json", "toml"])

    def test_choices_none_raises(self):
        msg = re.escape("Arg 'choices' cannot be None")
        with pytest.raises(ContractError, match=msg):
            g.ensure_in("yaml", None)  # type: ignore[arg-type]

class TestEnsureUsablePath:

    def test_accepts_non_empty_string(self):
        p = g.ensure_usable_path("config.yaml", "filename")
        assert isinstance(p, Path)
        assert str(p).endswith("config.yaml")

    def test_accepts_path(self):
        p = g.ensure_usable_path(Path("config.yaml"), "filename")
        assert p == Path("config.yaml")

    @pytest.mark.parametrize("bad_arg", ["", "   "])
    def test_rejects_empty_strings(self, bad_arg):
        msg = re.escape("Arg 'filename' cannot be an empty string")
        with pytest.raises(ContractError, match=msg):
            g.ensure_usable_path(bad_arg, "filename")

    def test_rejects_none(self):
        msg = re.escape("Arg 'filename' cannot be None")
        with pytest.raises(ContractError, match=msg):
            g.ensure_usable_path(None, "filename")

    def test_rejects_wrong_type(self):
        msg = re.escape("Arg 'filename' must be a Path or non-empty string\nDescription: filename\nReceived Type: int")
        with pytest.raises(ContractError, match=msg):
            g.ensure_usable_path(42, "filename")

class TestEnsureBooleanGuards:

    # ensure_true

    def test_ensure_true_passes_on_true(self):
        g.ensure_true(True, "should pass")

    def test_ensure_true_fails_on_false(self):
        msg = re.escape("Condition must be True")
        with pytest.raises(ContractError) as exc:
            g.ensure_true(False)
        assert re.search(msg, str(exc.value))

    @pytest.mark.parametrize("value", [1, [1], "yes", object()])
    def test_ensure_true_strict_non_bool_truthy_fails(self, value):
        with pytest.raises(ContractError):
            g.ensure_true(value)  # type: ignore[arg-type]

    def test_ensure_true_includes_description(self):
        msg = re.escape("Assertion failed: must be green")
        with pytest.raises(ContractError) as exc:
            g.ensure_true(False, "must be green")
        assert re.search(msg, str(exc.value))

    # ensure_false

    def test_ensure_false_passes_on_false(self):
        g.ensure_false(False, "should pass")

    def test_ensure_false_fails_on_true(self):
        msg = re.escape("Condition must be False")
        with pytest.raises(ContractError) as exc:
            g.ensure_false(True)
        assert re.search(msg, str(exc.value))

    @pytest.mark.parametrize("value", [0, "", [], {}, None])
    def test_ensure_false_strict_non_bool_falsy_fails(self, value):
        with pytest.raises(ContractError):
            g.ensure_false(value)  # type: ignore[arg-type]

    def test_ensure_false_includes_description(self):
        msg = re.escape("Assertion failed: must be red")
        with pytest.raises(ContractError) as exc:
            g.ensure_false(True, "must be red")
        assert re.search(msg, str(exc.value))
