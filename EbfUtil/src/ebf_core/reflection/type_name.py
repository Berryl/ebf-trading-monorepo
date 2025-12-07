# type_name.py
from __future__ import annotations

import types
from abc import ABC, abstractmethod
from typing import Any, Union, get_args, get_origin, List, Callable


# ============================================================================
# Core Formatters (Strategy Pattern)
# ============================================================================

class TypeFormatter(ABC):
    """Base class for type formatting strategies."""

    @abstractmethod
    def can_handle(self, typ: Any, origin: Any, args: tuple) -> bool:
        """Check if this formatter can handle the given type."""
        pass

    @abstractmethod
    def format(self, typ: Any, origin: Any, args: tuple, context: FormattingContext) -> str:
        """Format the type as a string."""
        pass


class FormattingContext:
    """Context for type formatting with shared configuration and utilities."""

    BUILTINS = {
        int: "int",
        str: "str",
        bool: "bool",
        float: "float",
        type(None): "None",
        list: "list",
        dict: "dict",
        tuple: "tuple",
        set: "set",
    }

    def __init__(self, show_generic_args: bool = True):
        self.show_generic_args = show_generic_args
        self.formatters: list[TypeFormatter] = [
            OptionalFormatter(),
            UnionFormatter(),
            CallableFormatter(),
            GenericFormatter(),
            PlainTypeFormatter(),
        ]

    def format_type(self, typ: Any) -> str:
        """Main entry point for formatting a type."""
        origin = get_origin(typ)
        args = get_args(typ)

        for formatter in self.formatters:
            if formatter.can_handle(typ, origin, args):
                return formatter.format(typ, origin, args, self)

        # Fallback
        return self.format_plain(typ)

    def format_plain(self, obj: Any) -> str:
        """Format a non-generic type or value."""
        if obj is Ellipsis:
            return "..."

        if isinstance(obj, type):
            return self.BUILTINS.get(obj, obj.__name__)

        # Try to handle objects without __name__
        try:
            if obj in self.BUILTINS:
                return self.BUILTINS[obj]
        except TypeError:
            pass

        return repr(obj)

    def format_args(self, args: tuple) -> list[str]:
        """Format a tuple of type arguments."""
        result = []
        for arg in args:
            # Handle Ellipsis especially to avoid it becoming "Ellipsis"
            if arg is Ellipsis:
                result.append("...")
            else:
                result.append(self.format_type(arg))
        return result


# ============================================================================
# Concrete Formatters
# ============================================================================

class OptionalFormatter(TypeFormatter):
    """Handles Optional[T] - Union[T, None] or T | None."""

    def can_handle(self, typ: Any, origin: Any, args: tuple) -> bool:
        return (
                origin in (Union, types.UnionType)
                and len(args) == 2
                and type(None) in args
        )

    def format(self, typ: Any, origin: Any, args: tuple, context: FormattingContext) -> str:
        non_none = next(a for a in args if a is not type(None))
        inner = context.format_type(non_none)
        return f"Optional[{inner}]"


class UnionFormatter(TypeFormatter):
    """Handles Union types with 3+ args or without None."""

    def can_handle(self, typ: Any, origin: Any, args: tuple) -> bool:
        return origin in (Union, types.UnionType)

    def format(self, typ: Any, origin: Any, args: tuple, context: FormattingContext) -> str:
        parts = context.format_args(args)
        return " | ".join(parts)


class CallableFormatter(TypeFormatter):
    """Handles Callable types with special parameter list formatting."""

    def can_handle(self, typ: Any, origin: Any, args: tuple) -> bool:
        return origin is not None and self._get_name(origin) == "Callable"

    def format(self, typ: Any, origin: Any, args: tuple, context: FormattingContext) -> str:
        if not context.show_generic_args:
            return "Callable"

        if not args:
            return "Callable[]"

        # Callable has a special structure: (param_list, return_type)
        parts = []
        for i, arg in enumerate(args):
            if i == 0:  # Parameter list
                parts.append(self._format_params(arg, context))
            else:  # Return type
                parts.append(context.format_type(arg))

        return f"Callable[{', '.join(parts)}]"

    def _format_params(self, params: Any, context: FormattingContext) -> str:
        """Format the parameter list for Callable."""
        if params is Ellipsis:
            return "[...]"

        if isinstance(params, (list, tuple)):
            if not params:
                return "[]"
            param_strs = [context.format_type(p) for p in params]
            return f"[{', '.join(param_strs)}]"

        return f"[{context.format_type(params)}]"

    def _get_name(self, origin: Any) -> str:
        return getattr(origin, "__name__", "")


class GenericFormatter(TypeFormatter):
    """Handles generic types like List[T], Dict[K, V], etc."""

    def can_handle(self, typ: Any, origin: Any, args: tuple) -> bool:
        return origin is not None

    def format(self, typ: Any, origin: Any, args: tuple, context: FormattingContext) -> str:
        base = getattr(origin, "__name__", str(origin))

        if not context.show_generic_args:
            return base

        if not args:
            return f"{base}[]"

        # Check for empty container markers
        if len(args) == 1 and args[0] == ():
            return f"{base}[]"

        parts = context.format_args(args)
        return f"{base}[{', '.join(parts)}]"


class PlainTypeFormatter(TypeFormatter):
    """Handles plain types without generic parameters."""

    def can_handle(self, typ: Any, origin: Any, args: tuple) -> bool:
        return True  # Always matches as fallback

    def format(self, typ: Any, origin: Any, args: tuple, context: FormattingContext) -> str:
        if typ in context.BUILTINS:
            return context.BUILTINS[typ]

        # Try to get __name__, but fall back to repr if it's None or missing
        if isinstance(typ, type):
            name = getattr(typ, "__name__", None)
            if name is not None:
                return name

        return repr(typ)


# ============================================================================
# Public API
# ============================================================================

def get_descriptive_type_name(
        typ: Any | None = None,
        *,
        default_if_none: str = "Type",
        show_generic_args: bool = True,
) -> str:
    """
    Generate a human-readable string representation of a type.

    Args:
        typ: The type to describe. If None, returns default_if_none.
        default_if_none: String to return when typ is None.
        show_generic_args: Whether to show generic type arguments.

    Returns:
        A string representation of the type.

    Examples:
        >>> get_descriptive_type_name(int)
        'int'
        >>> get_descriptive_type_name(List[str])
        'list[str]'
        >>> get_descriptive_type_name(Union[str, None])
        'Optional[str]'
        >>> get_descriptive_type_name(Callable[[int, str], bool])
        'Callable[[int, str], bool]'
    """
    if typ is None:
        return default_if_none

    context = FormattingContext(show_generic_args=show_generic_args)
    return context.format_type(typ)