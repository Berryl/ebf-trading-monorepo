from __future__ import annotations

from typing import Any, Callable, TypeVar

from ebf_core.reflection.type_name import get_descriptive_type_name


class TestGetDescriptiveTypeName:
    def test_none_returns_default(self) -> None:
        assert get_descriptive_type_name() == "Type"
        assert get_descriptive_type_name(None) == "Type"
        assert get_descriptive_type_name(default_if_none="Value") == "Value"

    def test_builtin_types(self) -> None:
        assert get_descriptive_type_name(int) == "int"
        assert get_descriptive_type_name(str) == "str"
        assert get_descriptive_type_name(list) == "list"
        assert get_descriptive_type_name(type(None)) == "None"

    def test_generic_types_with_args_shown(self) -> None:
        from typing import List, Dict, Tuple, Literal, Union

        assert get_descriptive_type_name(List[str]) == "list[str]"
        assert get_descriptive_type_name(Dict[str, int]) == "dict[str, int]"
        assert get_descriptive_type_name(Tuple[str, ...]) == "tuple[str, ...]"
        assert get_descriptive_type_name(Union[str, None]) == "Optional[str]"

        # CHANGED: Expect the actual values ('a', 'b', 42), not their types (str, int)
        # Note: Python's repr() usually uses single quotes for strings
        assert get_descriptive_type_name(Literal["a", "b", 42]) == "Literal['a', 'b', 42]"

    def test_generic_types_without_args_shown(self) -> None:
        from typing import List, Dict

        assert get_descriptive_type_name(List[str], show_generic_args=False) == "list"
        assert get_descriptive_type_name(Dict[str, int], show_generic_args=False) == "dict"

    def test_empty_generic_containers(self) -> None:
        from typing import List, Dict

        # list[] and dict[] are valid (though rare)
        empty_list: List[()] = []  # type: ignore[var-annotated]
        empty_dict: Dict[(), ()] = {}  # type: ignore[var-annotated]

        assert get_descriptive_type_name(List[()]) == "list[]"
        assert get_descriptive_type_name(Dict[(), ()]) == "dict[]"

    def test_complex_nested_generics(self) -> None:
        from typing import List, Dict

        assert (
                get_descriptive_type_name(List[Dict[str, List[int]]])
                == "list[dict[str, list[int]]]"
        )

    def test_special_cases(self) -> None:
        assert get_descriptive_type_name(Any) == "Any"
        assert get_descriptive_type_name(Callable[[str], int]) == "Callable[[str], int]"

        T = TypeVar("T")
        assert get_descriptive_type_name(list[T]) == "list[~T]"  # noqa or "list[T]" depending on Python version

    def test_fallback_to_repr_when_no_name(self) -> None:
        # Very rare case: some types have no __name__
        class WeirdType: ...

        del WeirdType.__name__  # simulate a broken type
        assert get_descriptive_type_name(WeirdType) == repr(WeirdType)

    def test_generic_origin_with_no_args(self) -> None:
        from typing import Sequence

        # Sequence without parameters
        assert get_descriptive_type_name(Sequence, show_generic_args=True) == "Sequence[]"
