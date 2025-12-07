# test_type_name.py
from __future__ import annotations

from typing import Any, Callable, Literal, TypeVar, Union, Tuple, List, Dict, Sequence, Set

from ebf_core.reflection.type_name import get_descriptive_type_name

T = TypeVar("T")


class TestGetDescriptiveTypeName:
    """Test suite for get_descriptive_type_name function."""

    # ========================================================================
    # Basic Type Tests
    # ========================================================================

    def test_none_returns_default(self) -> None:
        """Test that None input returns the default value."""
        assert get_descriptive_type_name() == "Type"
        assert get_descriptive_type_name(None) == "Type"
        assert get_descriptive_type_name(default_if_none="Something") == "Something"

    def test_builtin_types(self) -> None:
        """Test formatting of built-in Python types."""
        assert get_descriptive_type_name(int) == "int"
        assert get_descriptive_type_name(str) == "str"
        assert get_descriptive_type_name(bool) == "bool"
        assert get_descriptive_type_name(float) == "float"
        assert get_descriptive_type_name(list) == "list"
        assert get_descriptive_type_name(dict) == "dict"
        assert get_descriptive_type_name(tuple) == "tuple"
        assert get_descriptive_type_name(set) == "set"
        assert get_descriptive_type_name(type(None)) == "None"

    # ========================================================================
    # Generic Type Tests
    # ========================================================================

    def test_generic_types_with_single_arg(self) -> None:
        """Test generic types with a single type parameter."""
        assert get_descriptive_type_name(List[str]) == "list[str]"
        assert get_descriptive_type_name(Set[int]) == "set[int]"
        assert get_descriptive_type_name(Sequence[str]) == "Sequence[str]"

    def test_generic_types_with_multiple_args(self) -> None:
        """Test generic types with multiple type parameters."""
        assert get_descriptive_type_name(Dict[str, int]) == "dict[str, int]"
        assert get_descriptive_type_name(Tuple[int, str, bool]) == "tuple[int, str, bool]"

    def test_generic_types_with_ellipsis(self) -> None:
        """Test generic types with ellipsis (variable length)."""
        assert get_descriptive_type_name(Tuple[str, ...]) == "tuple[str, ...]"
        assert get_descriptive_type_name(Tuple[int, ...]) == "tuple[int, ...]"

    def test_literal_types(self) -> None:
        """Test Literal types with various values."""
        assert get_descriptive_type_name(Literal["a", "b", 42]) == "Literal['a', 'b', 42]"
        assert get_descriptive_type_name(Literal[True, False]) == "Literal[True, False]"

    def test_bare_generic_types(self) -> None:
        """Test bare generic types without type parameters."""
        assert get_descriptive_type_name(List) == "list[]"
        assert get_descriptive_type_name(Dict) == "dict[]"
        assert get_descriptive_type_name(Tuple) == "tuple[]"
        assert get_descriptive_type_name(Sequence) == "Sequence[]"

    # ========================================================================
    # Optional and Union Tests
    # ========================================================================

    def test_optional_types(self) -> None:
        """Test Optional[T] formatting (Union[T, None])."""
        assert get_descriptive_type_name(Union[str, None]) == "Optional[str]"
        assert get_descriptive_type_name(str | None) == "Optional[str]"
        assert get_descriptive_type_name(Union[int, None]) == "Optional[int]"
        assert get_descriptive_type_name(List[str] | None) == "Optional[list[str]]"

    def test_union_types(self) -> None:
        """Test Union types with multiple non-None types."""
        assert get_descriptive_type_name(Union[int, str]) == "int | str"
        assert get_descriptive_type_name(int | str | float) == "int | str | float"
        assert get_descriptive_type_name(int | str | None) == "int | str | None"

    # ========================================================================
    # Callable Tests
    # ========================================================================

    def test_callable_with_typed_params(self) -> None:
        """Test Callable types with typed parameters."""
        assert get_descriptive_type_name(Callable[[int, str], bool]) == "Callable[[int, str], bool]"
        assert get_descriptive_type_name(Callable[[int], str]) == "Callable[[int], str]"

    def test_callable_with_no_params(self) -> None:
        """Test Callable with no parameters."""
        assert get_descriptive_type_name(Callable[[], str]) == "Callable[[], str]"

    def test_callable_with_ellipsis(self) -> None:
        """Test Callable with ellipsis (any parameters)."""
        assert get_descriptive_type_name(Callable[..., int]) == "Callable[[...], int]"
        assert get_descriptive_type_name(Callable[..., str]) == "Callable[[...], str]"

    def test_callable_without_args_flag(self) -> None:
        """Test Callable formatting with show_generic_args=False."""
        assert get_descriptive_type_name(Callable[[int], str], show_generic_args=False) == "Callable"

    # ========================================================================
    # Nested and Complex Types
    # ========================================================================

    def test_nested_generics(self) -> None:
        """Test deeply nested generic types."""
        assert (
                get_descriptive_type_name(List[Dict[str, Tuple[int, ...]]])
                == "list[dict[str, tuple[int, ...]]]"
        )
        assert (
                get_descriptive_type_name(Dict[str, List[Union[int, str]]])
                == "dict[str, list[int | str]]"
        )

    def test_nested_optional(self) -> None:
        """Test Optional with nested generics."""
        assert get_descriptive_type_name(Union[List[int], None]) == "Optional[list[int]]"
        assert get_descriptive_type_name(Dict[str, int] | None) == "Optional[dict[str, int]]"

    # ========================================================================
    # TypeVar and Special Cases
    # ========================================================================

    def test_type_var(self) -> None:
        """Test TypeVar formatting."""
        assert get_descriptive_type_name(List[T]) == "list[~T]"  # type: ignore[valid-type]
        assert get_descriptive_type_name(Dict[str, T]) == "dict[str, ~T]"  # type: ignore[valid-type]

    def test_show_generic_args_false(self) -> None:
        """Test that show_generic_args=False hides type parameters."""
        assert get_descriptive_type_name(List[str], show_generic_args=False) == "list"
        assert get_descriptive_type_name(Dict[str, int], show_generic_args=False) == "dict"
        assert get_descriptive_type_name(Tuple[int, str], show_generic_args=False) == "tuple"

    def test_custom_classes(self) -> None:
        """Test formatting of custom class types."""

        class CustomClass:
            pass

        assert get_descriptive_type_name(CustomClass) == "CustomClass"
        assert get_descriptive_type_name(List[CustomClass]) == "list[CustomClass]"

    def test_fallback_to_repr(self) -> None:
        """Test fallback to repr for objects without proper __name__."""

        class CustomObject:
            def __repr__(self):
                return "<CustomRepr>"

        obj = CustomObject()
        result = get_descriptive_type_name(obj)
        assert result == "<CustomRepr>"

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_any_type(self) -> None:
        """Test the Any type."""
        # Any is special - it has no origin but gets formatted
        result = get_descriptive_type_name(Any)
        assert "Any" in result or "typing.Any" in result

    def test_none_type_directly(self) -> None:
        """Test NoneType directly."""
        assert get_descriptive_type_name(type(None)) == "None"


class TestFormattingContext:
    """Test the FormattingContext class directly."""

    def test_format_plain_with_ellipsis(self) -> None:
        """Test that Ellipsis is formatted correctly."""
        from ebf_core.reflection.type_name import FormattingContext

        ctx = FormattingContext()
        assert ctx.format_plain(Ellipsis) == "..."

    def test_format_plain_with_builtin(self) -> None:
        """Test formatting of builtin types."""
        from ebf_core.reflection.type_name import FormattingContext

        ctx = FormattingContext()
        assert ctx.format_plain(int) == "int"
        assert ctx.format_plain(str) == "str"


class TestFormatterIndividually:
    """Test individual formatter classes."""

    def test_optional_formatter_recognition(self) -> None:
        """Test that OptionalFormatter correctly identifies Optional types."""
        from ebf_core.reflection.type_name import OptionalFormatter, FormattingContext
        from typing import get_origin, get_args

        formatter = OptionalFormatter()
        ctx = FormattingContext()

        typ = Union[str, None]
        origin = get_origin(typ)
        args = get_args(typ)

        assert formatter.can_handle(typ, origin, args)
        assert formatter.format(typ, origin, args, ctx) == "Optional[str]"

    def test_union_formatter_with_three_types(self) -> None:
        """Test UnionFormatter with 3+ types."""
        from ebf_core.reflection.type_name import UnionFormatter, FormattingContext
        from typing import get_origin, get_args

        formatter = UnionFormatter()
        ctx = FormattingContext()

        typ = Union[int, str, float]
        origin = get_origin(typ)
        args = get_args(typ)

        assert formatter.can_handle(typ, origin, args)
        result = formatter.format(typ, origin, args, ctx)
        assert result == "int | str | float"
