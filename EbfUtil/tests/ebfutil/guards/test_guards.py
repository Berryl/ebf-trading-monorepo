import re

import pytest

from ebfutil.guards import guards as g


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
        with pytest.raises(AssertionError, match=msg):
            g.ensure_type("not a number", int, "count")

    def test_simple_type_mismatch_when_no_description(self):
        msg = re.escape("Value must be of type int (it was type str)")
        with pytest.raises(AssertionError, match=msg):
            g.ensure_type("not a number", int)

    def test_parameter_of_none(self):
        msg = re.escape("Value must be of type int (it was type None)")
        with pytest.raises(AssertionError, match=msg):
            g.ensure_type(None, int)

    def test_complex_type_mismatch(self):
        msg = re.escape("Arg 'numbers': item 0 of list is not an instance of int")
        with pytest.raises(AssertionError, match=msg):
            g.ensure_type(["1", "2", "3"], list[int], "numbers")

    def test_complex_type_mismatch_when_no_description(self):
        msg = re.escape("Value: item 0 of list is not an instance of int")
        with pytest.raises(AssertionError, match=msg):
            g.ensure_type(["1", "2", "3"], list[int])

    def test_nested_type_mismatch(self):
        msg = re.escape("Arg 'matrix': item 0 of item 0 of list is not an instance of int")
        with pytest.raises(AssertionError, match=msg):
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
        with pytest.raises(AssertionError, match=msg):
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
        with pytest.raises(AssertionError, match=msg):
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
        with pytest.raises(AssertionError, match=msg):
            g.ensure_not_empty_str(value, desc_param)


class TestEnsureAttribute:

    def test_when_attribute_exists(self):
        class Example:
            value = 42

        g.ensure_attribute(Example(), "value", "example_value")
        pass  # No exception should be raised

    def test_when_attribute_does_not_exist_with_description(self):
        class Example:
            pass

        expected_msg = re.escape("example_value") + r"\nObject type: Example\nRequested attribute: missing_attr"

        with pytest.raises(AttributeError) as exc_info:
            g.ensure_attribute(Example(), "missing_attr", "example_value")

        # Extract actual error message
        actual_message = str(exc_info.value)

        # Use regex search instead of match to allow for extra lines
        assert re.search(expected_msg, actual_message)

    def test_when_attribute_does_not_exist_without_description(self):
        class Example:
            pass

        expected_msg = re.escape("Example has no attribute 'missing_attr'")

        with pytest.raises(AttributeError) as exc_info:
            g.ensure_attribute(Example(), "missing_attr")

        actual_message = str(exc_info.value)

        assert re.search(expected_msg, actual_message)

    def test_when_attribute_is_none(self):
        class Example:
            value = None

        g.ensure_attribute(Example(), "value", "example_value")
        pass  # No exception should be raised (presence is checked, not value)

    def test_when_candidate_is_none(self):
        msg = re.escape("Arg 'example_value' cannot be None")
        with pytest.raises(AssertionError, match=msg):
            g.ensure_attribute(None, "missing_attr", "example_value")
