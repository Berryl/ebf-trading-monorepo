import copy
import weakref
from dataclasses import dataclass

import pytest
from src.ebf_core.reflection.attr_reflector import AttributeReflector


class TestSimpleAttr:
    """Tests for basic get/set operations on simple attributes."""

    class SimpleClass:  # ← Defined here, inside the test class
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

    def test_none_values(self, sut, simple_obj: SimpleClass):
        assert sut.get_value("nested_attr") == "original_value"
        sut.set_value("nested_attr", None)

        assert sut.get_value("nested_attr") is None
        assert sut.has_attr("nested_attr"), "Attribute with None as a value should exist"


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


class TestNoneValueHandling:
    """Tests for handling attributes with None values."""

    @pytest.fixture
    def person(self):
        """Fixture providing a person object with None name."""

        class Person:
            def __init__(self):
                self.name = None

        return Person()

    @pytest.fixture
    def reflector(self, person):
        """Fixture providing a reflector for the person object."""
        return AttributeReflector(person)

    def test_has_attr_returns_true_for_none_value(self, reflector):
        """Test has_attr returns True for attribute that exists but is None."""
        assert reflector.has_attr("name") is True

    def test_can_get_none_value(self, reflector):
        """Test getting an attribute that exists but is None."""
        assert reflector.get_value("name") is None

    def test_can_set_none_value(self, reflector, person):
        """Test setting an attribute that was initially None."""
        reflector.set_value("name", "Ted")
        assert person.name == "Ted"


class TestErrorHandling:
    """Tests for error handling and validation."""

    def test_get_non_existent_attribute_raises_error(self):
        """Test that getting a non-existent attribute raises AttributeError."""

        class SimpleClass:
            def __init__(self):
                self.existing_attr = "some_value"

        obj = SimpleClass()
        reflector = AttributeReflector(obj)
        err_msg = "'SimpleClass' object has no attribute 'non_existent_attr'"

        with pytest.raises(AttributeError, match=err_msg):
            reflector.get_value("non_existent_attr")

    def test_set_non_existent_attribute_raises_error(self):
        """Test that setting a non-existent attribute raises AttributeError."""

        class SimpleClass:
            def __init__(self):
                self.existing_attr = "some_value"

        obj = SimpleClass()
        reflector = AttributeReflector(obj)

        with pytest.raises(AttributeError):
            reflector.set_value("non_existent_attr", "new_value")

    def test_get_with_none_path_raises_error(self):
        """Test that passing None as attr_path raises AssertionError."""

        class SimpleClass:
            def __init__(self):
                self.existing_attr = "some_value"

        obj = SimpleClass()
        reflector = AttributeReflector(obj)
        err_msg = "Parameter 'attr_path' must be valued"

        with pytest.raises(AssertionError, match=err_msg):
            reflector.get_value(None)

    def test_set_with_none_path_raises_error(self):
        """Test that passing None as attr_path to set_value raises AssertionError."""

        class SimpleClass:
            def __init__(self):
                self.existing_attr = "some_value"

        obj = SimpleClass()
        reflector = AttributeReflector(obj)
        err_msg = "Parameter 'attr_path' must be valued"

        with pytest.raises(AssertionError, match=err_msg):
            reflector.set_value(None, "blah")

    def test_has_attr_with_none_path_raises_error(self):
        """Test that passing None as attr_path to has_attr raises AssertionError."""

        class SimpleClass:
            def __init__(self):
                self.existing_attr = "some_value"

        obj = SimpleClass()
        reflector = AttributeReflector(obj)
        err_msg = "Parameter 'attr_path' must be valued"

        with pytest.raises(AssertionError, match=err_msg):
            reflector.has_attr(None)


class TestWeakMethodReferences:
    """Tests for handling weak method references."""

    def test_reflector_handles_weak_method_get(self):
        """Test that weak method references are resolved to tuple format on get."""

        class MyClass:
            def __init__(self):
                self.weak_method = None

            def my_method(self):
                pass

        obj = MyClass()
        reflector = AttributeReflector(obj)

        # Create and set a weak method reference
        weak_method_ref = weakref.WeakMethod(obj.my_method)
        reflector.set_value('weak_method', weak_method_ref)

        # Get the weak method and verify tuple format
        result = reflector.get_value('weak_method')

        assert isinstance(result, tuple)
        assert result[0] == '__weakmethod__'
        assert result[1] == 'my_method'
        assert isinstance(result[2], int)  # id of the instance

    def test_weak_method_with_deepcopy(self):
        """Test that weak methods are handled correctly during deep copy operations."""

        class TestClass:
            def __init__(self):
                self.weak_method = None

            def test_method(self):
                pass

            def __deepcopy__(self, memo):
                new_instance = TestClass()
                for k, v in self.__dict__.items():
                    if k != 'weak_method':
                        setattr(new_instance, k, copy.deepcopy(v, memo))
                if self.weak_method is not None:
                    new_instance.weak_method = weakref.WeakMethod(new_instance.test_method)
                return new_instance

        obj = TestClass()
        obj.weak_method = weakref.WeakMethod(obj.test_method)

        reflector = AttributeReflector(obj)
        reflector.set_value('weak_method', obj.weak_method)

        # Verify weak method format
        result = reflector.get_value('weak_method')
        assert isinstance(result, tuple)
        assert result[0] == '__weakmethod__'

        # Test deep copy behavior
        copied = copy.deepcopy(obj)
        assert hasattr(copied, 'weak_method')
        assert isinstance(copied.weak_method, weakref.WeakMethod)


class TestDataclassSupport:
    """Tests for working with dataclass instances."""

    def test_dataclass_attribute_access(self):
        """Test accessing attributes of a dataclass instance."""

        @dataclass
        class NestedClass:
            inner_attr: str = "inner_value"

        class MyClass:
            def __init__(self):
                self.nested_instance = NestedClass()

        obj = MyClass()
        reflector = AttributeReflector(obj)

        # Get the value directly through dot notation
        result = reflector.get_value("nested_instance.inner_attr")
        assert result == "inner_value"

    def test_dataclass_attribute_modification(self):
        """Test modifying attributes of a dataclass instance."""

        @dataclass
        class NestedClass:
            inner_attr: str = "inner_value"

        class MyClass:
            def __init__(self):
                self.nested_instance = NestedClass()

        obj = MyClass()
        reflector = AttributeReflector(obj)

        # Set the value through dot notation
        reflector.set_value("nested_instance.inner_attr", "new_value")
        assert obj.nested_instance.inner_attr == "new_value"

    def test_dataclass_has_attr(self):
        """Test checking attribute existence in a dataclass instance."""

        @dataclass
        class NestedClass:
            inner_attr: str = "inner_value"

        class MyClass:
            def __init__(self):
                self.nested_instance = NestedClass()

        obj = MyClass()
        reflector = AttributeReflector(obj)

        assert reflector.has_attr("nested_instance.inner_attr") is True
        assert reflector.has_attr("nested_instance.non_existent") is False


class TestComplexScenarios:
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

        reflector = AttributeReflector(obj)

        # Test getting through complex path
        result = reflector.get_value("level1.level2.0.item.value")
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
        reflector = AttributeReflector(obj)

        assert reflector.get_value("items.0.name") == "first"
        assert reflector.get_value("items.1.name") == "second"
        assert reflector.get_value("items.2.name") == "third"

        reflector.set_value("items.1.name", "modified")
        assert obj.items[1].name == "modified"
