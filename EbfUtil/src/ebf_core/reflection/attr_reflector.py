import weakref
from typing import Any

import src.ebf_core.guards.guards as g


class AttributeReflector:
    """
    Provides functionality to get, set, and check for both simple and nested attributes in an object.

    This class allows accessing and modifying attributes within an object
    using a dot-separated attribute path. It supports attribute access, list indexing,
    and dictionary key access for nested objects.

    Notes: functions have been written iteratively, not recursively. This is more performant and easier to debug.
    """

    def __init__(self, instance: object):
        self.instance = instance

    def set_value(self, attr_path: str, value: Any) -> None:
        """
        Sets the value of a nested attribute specified by `attr_path`.

        :param attr_path: A dot-separated string indicating the path to the attribute.
        :param value: The value to set at the specified attribute path.
        :raises AttributeError: If the attribute does not exist and cannot be set.
        """
        g.ensure_not_empty_str(attr_path, "attr_path")


        attrs = attr_path.split(".")
        obj = self.instance

        for i, attr in enumerate(attrs):
            if i == len(attrs) - 1:  # Last attribute
                if isinstance(obj, dict):
                    obj[attr] = value
                elif isinstance(obj, list):
                    self._set_list_value(obj, attr, value)
                elif hasattr(obj, attr):
                    setattr(obj, attr, value)
                else:
                    raise AttributeError(f"'{type(obj).__name__}' object has no attribute '{attr}'")
                break

            obj = self._traverse_to_next_obj(obj, attr)

    def get_value(self, attr_path: str) -> Any:
        """
        Retrieves the value of a nested attribute specified by `attr_path`.

        :param attr_path: A dot-separated string indicating the path to the attribute.
        :return: The value of the attribute, or None if the attribute doesn't exist or is None.
        :raises AttributeError: If the attribute path is invalid or does not exist.
        """
        g.ensure_not_empty_str(attr_path, "attr_path")

        attrs = attr_path.split(".")
        obj = self.instance

        for i, attr in enumerate(attrs):
            try:
                obj = self._traverse_to_next_obj(obj, attr, create_missing=False)

                # Resolve weak references only if obj is not None
                if obj is not None:
                    obj = self._resolve_weak_method(obj)
            except (AttributeError, KeyError, IndexError):
                raise AttributeError(f"'{type(self.instance).__name__}' object has no attribute '{attr_path}'")

            # If the attribute is None but exists, break and return None
            if obj is None and i < len(attrs) - 1:
                raise AttributeError(f"'{type(self.instance).__name__}' object has no attribute '{attr_path}'")

        return obj

    def has_attr(self, attr_path: str) -> bool:
        """
        Checks if the nested attribute specified by `attr_path` exists.

        :param attr_path: A dot-separated string indicating the path to the attribute.
        :return: True if the attribute exists, False otherwise.
        """
        g.ensure_not_empty_str(attr_path, "attr_path")

        attrs = attr_path.split(".")
        obj = self.instance

        for attr in attrs:
            try:
                obj = self._traverse_to_next_obj(obj, attr, create_missing=False)

                # Only resolve weak references if obj is not None
                if obj is not None:
                    obj = self._resolve_weak_method(obj)
            except (AttributeError, KeyError, IndexError):
                return False

            # If obj is None after traversing, return True (attribute exists but is None)
            if obj is None:
                return True

        return True

    # region helpers

    @staticmethod
    def _set_list_value(obj, attr, value) -> None:
        """
        Set a value in a list at the specified index.

        :param obj: The list object.
        :param attr: The index as a string.
        :param value: The value to set at the specified index.
        :raises IndexError: If the index is invalid.
        """
        try:
            index = int(attr)
            obj[index] = value
        except (ValueError, IndexError):
            raise IndexError(f"Invalid index '{attr}' for list")

    @staticmethod
    def _get_list_element(obj, attr, create_missing: bool = True):
        """
        Get a list element by index. Optionally, create missing elements.

        :param obj: The list object.
        :param attr: The index as a string.
        :param create_missing: Whether to create missing elements.
        :return: The value at the specified index.
        :raises IndexError: If the index is invalid.
        """
        try:
            index = int(attr)
            if index >= len(obj):
                if create_missing:
                    obj.extend([None] * (index - len(obj) + 1))
                else:
                    raise IndexError(f"Index '{index}' out of bounds for list")
            return obj[index]
        except ValueError:
            raise IndexError(f"Invalid index '{attr}' for list")

    def _traverse_to_next_obj(self, obj, attr, create_missing: bool = True):
        """
        Traverse to the next object in the attribute path. Optionally, create missing entries.

        :param obj: The current object in the traversal.
        :param attr: The attribute or key to traverse.
        :param create_missing: If True, create missing dictionaries or list entries. If False, check existence only.
        :return: The next object in the attribute path.
        :raises AttributeError: If the attribute does not exist.
        :raises KeyError: If the key does not exist in a dictionary.
        :raises IndexError: If the index does not exist in a list.
        """
        if isinstance(obj, dict):
            if attr not in obj:
                if create_missing:
                    obj[attr] = {}
                else:
                    raise KeyError(f"Key '{attr}' not found in dictionary")
            return obj[attr]
        elif isinstance(obj, list):
            return self._get_list_element(obj, attr, create_missing)
        elif hasattr(obj, attr):
            next_obj = getattr(obj, attr)
            if next_obj is None and create_missing:
                setattr(obj, attr, {})
                return getattr(obj, attr)
            return next_obj
        else:
            raise AttributeError(f"'{type(obj).__name__}' object has no attribute '{attr}'")

    @staticmethod
    def _resolve_weak_method(obj):
        """
        Resolves a weak method reference to its actual method if it still exists.

        :param obj: The object to check and resolve if it is a weak method.
        :return: A tuple representation of the weak method if available, otherwise None.
        """
        if isinstance(obj, weakref.WeakMethod):
            callback = obj()
            if callback is None:
                return None
            if hasattr(callback, "__func__") and hasattr(callback, "__self__"):
                return '__weakmethod__', callback.__func__.__name__, id(callback.__self__)
            else:
                raise AttributeError(f"WeakMethod callback is missing expected attributes: '__func__' or '__self__'")
        return obj

    # endregion
