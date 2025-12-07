import types
from typing import get_origin, get_args, Union, Callable, Literal, Any


def get_descriptive_type_name(
        type_: Any = None,
        *,
        default_if_none: str = "Type",
        show_generic_args: bool = True,
) -> str:
    """
    Return a clean, human-readable name for a type.
    """
    if type_ is None:
        return default_if_none

    # ── Special case: Optional[T] ──────────────────────────────────────
    origin = get_origin(type_)
    # Handle both typing.Union and Python 3.10+ "|" operator (types.UnionType)
    if origin is Union or origin is types.UnionType:
        args = get_args(type_)
        if len(args) == 2:
            arg_set = set(args)
            if type(None) in arg_set or None in arg_set:
                # Identify the non-None argument
                non_none = next((a for a in args if a is not type(None) and a is not None), None)
                if non_none:
                    inner = get_descriptive_type_name(non_none, show_generic_args=True)
                    return f"Optional[{inner}]"

        # If it's a Union but not Optional (or Optional with >2 args),
        # let's format it as Union[A, B] or A | B depending on preference.
        # Here we stick to the class name logic below, but we must handle
        # UnionType having no __name__.
        if origin is types.UnionType:
            # UnionType doesn't have __name__, so we treat it manually
            if show_generic_args:
                formatted_args = [get_descriptive_type_name(a) for a in args]
                return " | ".join(formatted_args)
            return "Union"

    # ── Handle Generic Origins ─────────────────────────────────────────
    if origin is not None:
        if not show_generic_args:
            return getattr(origin, "__name__", str(origin))

        raw_args = get_args(type_)
        arg_strings = []

        # Special handling for Literal: args are values, not types
        if origin is Literal:
            arg_strings = [repr(a) for a in raw_args]
        else:
            for arg in raw_args:
                if arg is Ellipsis:
                    arg_strings.append("...")
                # Special handling for Callable arguments which can be a list: Callable[[A, B], R]
                elif isinstance(arg, list):
                    fn_args = [get_descriptive_type_name(a) for a in arg]
                    arg_strings.append(f"[{', '.join(fn_args)}]")
                else:
                    arg_strings.append(get_descriptive_type_name(arg))

        args_part = ", ".join(arg_strings)
        base_name = getattr(origin, "__name__", str(origin))

        # Tuple prettification
        if origin is tuple:
            if not raw_args:
                return "tuple[]"
            if raw_args == (Ellipsis,):
                return "tuple[...]"

        if args_part:
            return f"{base_name}[{args_part}]"
        return f"{base_name}[]"

    # ── Plain built-in types & Fallbacks ───────────────────────────────
    if type_ is type(None):
        return "None"

    if hasattr(type_, "__name__"):
        return type_.__name__

    # Fallback
    return repr(type_)