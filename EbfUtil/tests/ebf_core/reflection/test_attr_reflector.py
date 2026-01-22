import copy
import weakref
from dataclasses import dataclass

import pytest
from src.ebf_core.guards.guards import ContractError
from src.ebf_core.reflection.attr_reflector import AttributeReflector


class TestSimpleAttr:
    """Tests for basic get/set operations on simple attributes."""

    class SimpleClass:
        def __init__(self):
            self.attr = "original_value"
            self.nested_attr = "original_value"  # for the combined test

    @pytest.fixture
    def simple_obj(self) -> object:
        return TestSimpleAttr.SimpleClass()

    @pytest.fixture
    def sut(self, simple_obj) -> AttributeReflector:
        return AttributeReflector(simple_obj)

    def test_has_attr(self, sut):
        assert sut.has_attr("attr")
        assert not sut.has_attr("not_an_attr")

    def test_can_get_value(self, sut):
        assert sut.get_value("attr") == "original_value"

    def test_can_set_value(self, sut, simple_obj: SimpleClass):
        sut.set_value("attr", "new_value")
        assert simple_obj.attr == "new_value"

    def test_get_and_set_combined(self, sut, simple_obj: SimpleClass):
        """Test combined get and set operations."""
        assert sut.get_value("nested_attr") == "original_value"
        sut.set_value("nested_attr", "new_value")
        assert simple_obj.nested_attr == "new_value"

    def test_none_values(self, sut):
        assert sut.get_value("nested_attr") == "original_value"
        sut.set_value("nested_attr", None)

        assert sut.get_value("nested_attr") is None
        assert sut.has_attr("nested_attr"), "Attribute with None as a value should exist"

    @pytest.mark.parametrize("illegal_arg", [None, "", "  "])
    def test_non_existent_attribute_spec_raises_error(self, sut, illegal_arg):
        with pytest.raises(ContractError):
            sut.get_value(illegal_arg)

        with pytest.raises(ContractError):
            sut.set_value(illegal_arg, "blah")


class TestNestedAttrs:
    """Tests for accessing nested attributes through dot notation."""

    class GrandparentClass:
        def __init__(self):
            self.name = "grandpa"

    class ParentClass(GrandparentClass):
        def __init__(self):
            super().__init__()
            self.name = "parent"
            self.ancestor = TestNestedAttrs.GrandparentClass()

    class ChildClass(ParentClass):
        def __init__(self):
            super().__init__()
            self.name = "child"
            self.ancestor = TestNestedAttrs.ParentClass()

    @pytest.fixture
    def ancestor(self) -> object:
        return TestNestedAttrs.GrandparentClass()

    @pytest.fixture
    def parent(self) -> object:
        return TestNestedAttrs.ParentClass()

    @pytest.fixture
    def child(self) -> object:
        return TestNestedAttrs.ChildClass()

    @pytest.fixture
    def sut(self, child) -> AttributeReflector:
        return AttributeReflector(child)

    def test_has_attr(self, sut):
        assert sut.has_attr("ancestor.ancestor.name")
        assert not sut.has_attr("ancestor.not_an_attr")

    def test_get_value(self, sut, child: ChildClass):
        assert sut.get_value("name") == "child"
        assert sut.get_value("ancestor.name") == "parent"
        assert sut.get_value("ancestor.ancestor.name") == "grandpa"

    def test_set_value(self, sut, child: ChildClass):
        assert sut.get_value("ancestor.ancestor.name") == "grandpa"

        sut.set_value("ancestor.ancestor.name", "Herbie")
        assert sut.get_value("ancestor.ancestor.name") == "Herbie"


class TestDictionaryAttr:
    """Tests for accessing dictionary keys through dot notation."""

    class MyClass:
        def __init__(self):
            self.dict_attr = {"key1": 22, "key2": 33}

    @pytest.fixture
    def obj_with_dict(self) -> object:
        return TestDictionaryAttr.MyClass()

    @pytest.fixture
    def sut(self, obj_with_dict) -> AttributeReflector:
        return AttributeReflector(obj_with_dict)

    def test_has_attr(self, sut):
        assert sut.has_attr("dict_attr.key1")
        assert not sut.has_attr("dict_attr.key99")

    def test_get_value(self, sut):
        assert sut.get_value("dict_attr.key1") == 22
        assert sut.get_value("dict_attr.key2") == 33

    def test_set_value(self, sut):
        assert sut.get_value("dict_attr.key1") == 22

        sut.set_value("dict_attr.key1", 44)
        assert sut.get_value("dict_attr.key1") == 44
        assert sut.get_value("dict_attr") == {'key1': 44, 'key2': 33}


class TestListAttr:
    """Tests for accessing list elements through dot notation with indices."""

    class MyClass:
        def __init__(self):
            self.list_attr = [1, 2, 3]

    @pytest.fixture
    def obj_with_list(self) -> object:
        return TestListAttr.MyClass()

    @pytest.fixture
    def sut(self, obj_with_list) -> AttributeReflector:
        return AttributeReflector(obj_with_list)

    def test_has_attr(self, sut):
        assert sut.has_attr("list_attr.0")
        assert not sut.has_attr("list_attr.99")

    def test_get_value(self, sut):
        assert sut.get_value("list_attr.0") == 1
        assert sut.get_value("list_attr.1") == 2
        assert sut.get_value("list_attr.2") == 3

    def test_set_value(self, sut, obj_with_list):
        assert sut.get_value("list_attr.1") == 2

        sut.set_value("list_attr.1", 99)
        assert sut.get_value("list_attr.1") == 99
        assert sut.get_value("list_attr") == [1, 99, 3]


class TestWeakMethodReferences:
    """Tests for handling weak method references."""

    class MyClass:
        def __init__(self):
            self.weak_method = None

        def my_method(self):
            pass

    class DeepCopyClass:
        def __init__(self):
            self.weak_method = None

        def test_method(self):
            pass

        def __deepcopy__(self, memo):
            new_instance = TestWeakMethodReferences.DeepCopyClass()
            for k, v in self.__dict__.items():
                if k != 'weak_method':
                    setattr(new_instance, k, copy.deepcopy(v, memo))
            if self.weak_method is not None:
                new_instance.weak_method = weakref.WeakMethod(new_instance.test_method)
            return new_instance

    @pytest.fixture
    def obj(self) -> object:
        return TestWeakMethodReferences.MyClass()

    @pytest.fixture
    def sut(self, obj) -> AttributeReflector:
        return AttributeReflector(obj)

    def test_get_value(self, sut, obj):
        """Test that weak method references are resolved to tuple format on get."""
        weak_method_ref = weakref.WeakMethod(obj.my_method)  # noqa
        sut.set_value('weak_method', weak_method_ref)

        result = sut.get_value('weak_method')

        assert isinstance(result, tuple)
        assert result[0] == '__weakmethod__'
        assert result[1] == 'my_method'
        assert isinstance(result[2], int)

    def test_when_deepcopy(self):
        """Test that weak methods are handled correctly during deep copy operations."""
        obj = TestWeakMethodReferences.DeepCopyClass()
        obj.weak_method = weakref.WeakMethod(obj.test_method)

        sut = AttributeReflector(obj)
        sut.set_value('weak_method', obj.weak_method)

        result = sut.get_value('weak_method')
        assert isinstance(result, tuple)
        assert result[0] == '__weakmethod__'

        copied = copy.deepcopy(obj)
        assert hasattr(copied, 'weak_method')
        assert isinstance(copied.weak_method, weakref.WeakMethod)


class TestDataclassSupport:
    """Tests for working with dataclass instances."""

    @dataclass
    class SimpleClass:
        attr: str

    @pytest.fixture
    def dataclass_obj(self) -> object:
        return TestDataclassSupport.SimpleClass("original value")

    @pytest.fixture
    def sut(self, dataclass_obj) -> AttributeReflector:
        return AttributeReflector(dataclass_obj)

    def test_attr_usage_is_same_as_regular_class(self, sut):
        assert sut.has_attr("attr")
        assert not sut.has_attr("not_an_attr")

        assert sut.get_value("attr") == "original value"

        sut.set_value("attr", "new value")
        assert sut.get_value("attr") == "new value"


class TestMixedComplexObjects:
    """Tests for complex nested scenarios mixing different types."""

    def test_mixed_dict_list_object_nesting(self):
        """Test accessing deeply nested structures with mixed types."""

        class InnerClass:
            def __init__(self):
                self.value = "deep_value"

        obj = {
            "level1": {
                "level2": [
                    {"item": InnerClass()}
                ]
            }
        }

        sut = AttributeReflector(obj)

        result = sut.get_value("level1.level2.0.item.value")
        assert result == "deep_value"

    def test_list_of_objects_access(self):
        """Test accessing objects within a list."""

        class Item:
            def __init__(self, name):
                self.name = name

        class Container:
            def __init__(self):
                self.items = [Item("first"), Item("second"), Item("third")]

        obj = Container()
        sut = AttributeReflector(obj)

        assert sut.get_value("items.0.name") == "first"
        assert sut.get_value("items.1.name") == "second"
        assert sut.get_value("items.2.name") == "third"

        sut.set_value("items.1.name", "modified")
        assert obj.items[1].name == "modified"
