import traceback
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar, NoReturn

from ebf_core.reflection.type_name import get_descriptive_type_name
from typeguard import (
    CollectionCheckStrategy,
    ForwardRefPolicy,
    TypeCheckError,
    check_type,
)


def ensure_not_none(candidate: Any, description: str | None = None) -> None:
    """
    Ensures that the candidate is not None, raising a ContractError if it is.
    """
    if candidate is None:
        prefix = f"Arg '{description}'" if description else "Value"
        _fail(
            message=f"{prefix} cannot be None",
            Description=description or "Unnamed",
            Received="None",
        )


T = TypeVar('T')


def ensure_type(candidate: Any, expected_type: type[T], description: str | None = None) -> T:
    """
    Ensures that the candidate is of the expected type, raising a ContractError if not.
    """
    try:
        check_type(
            value=candidate,
            expected_type=expected_type,
            forward_ref_policy=ForwardRefPolicy.ERROR,
            collection_check_strategy=CollectionCheckStrategy.ALL_ITEMS,
        )
        return candidate
    except TypeCheckError as e:
        actual_type = type(candidate).__name__ if candidate is not None else "None"
        prefix = f"Arg '{description}'" if description else "Value"

        # Use the new function for a better name
        expected_name = get_descriptive_type_name(expected_type)

        # For generics, still leverage type-guard's detailed message if available
        if hasattr(expected_type, "__origin__"):
            message = f"{prefix}: {e}"
        else:
            message = f"{prefix} must be of type {expected_name} (it was type {actual_type})"

        _fail(
            message=message,
            Description=description or "Unnamed",
            Expected_Type=expected_name,
            Received_Type=actual_type,
        )


def ensure_attribute(candidate: Any, attr_spec: str, description: str | None = None, ) -> T:
    """
    Ensures that the candidate has the specified attribute.
    """
    ensure_not_none(candidate, description)

    if not hasattr(candidate, attr_spec):
        description_str = description or f"{type(candidate).__name__}"
        available_attrs = sorted(dir(candidate))
        attr_list = ", ".join(available_attrs[:20])
        if len(available_attrs) > 20:
            attr_list += ", ..."

        _fail(
            message=f"{description_str} has no attribute '{attr_spec}'",
            Description=description or "Unnamed",
            Object_type=type(candidate).__name__,
            Requested_attribute=attr_spec,
            Available_attributes=attr_list,
        )

    return candidate  # type: ignore[return-value]


def ensure_in(candidate: Any, choices: Iterable[Any], description: str | None = None, ) -> None:
    """
    Ensures that the candidate is a member of the provided choices.
    """
    ensure_not_none(choices, "choices")

    if candidate in choices:
        return

    # Build a nice preview of allowed values
    try:
        items = list(iter(choices))
        preview = ", ".join(repr(x) for x in items[:20])
        if len(items) > 20:
            preview += ", ..."
    except Exception:  # noqa: no cover — defensive, very rare
        preview = "<unprintable>"

    prefix = f"Arg '{description}'" if description else "Value"

    _fail(
        message=f"{prefix} must be one of the allowed choices",
        Description=description or "Unnamed",
        Received=candidate,
        Allowed_sample=preview or "(empty)",
    )


def ensure_usable_path(candidate: Any, description: str | None = None, ) -> Path:
    """
    Ensures that the candidate is either a non-empty string or a PathLib.Path.
    Returns a Path object.
    """
    ensure_not_none(candidate, description)

    if isinstance(candidate, Path):
        if not str(candidate).strip():
            prefix = f"Arg '{description}'" if description else "Value"
            _fail(
                message=f"{prefix} cannot be an empty path",
                Description=description or "Unnamed",
                Received="Empty Path",
            )
        return candidate

    if isinstance(candidate, str):
        ensure_str_is_valued(candidate, description)
        return Path(candidate)

    prefix = f"Arg '{description}'" if description else "Value"
    _fail(
        message=f"{prefix} must be a Path or non-empty string",
        Description=description or "Unnamed",
        **{"Received Type": type(candidate).__name__},
    )


# region numbers
def ensure_positive_number(
        candidate: Any,
        *,
        description: str | None = None,
        allow_zero: bool = False,
        strict: bool = False,
) -> int | float:
    """
    Ensures the value is a positive number (> 0 or >= 0 if allow_zero=True).

    Args:
        candidate: The value to check
        description: Optional name for better error messages
        allow_zero: If True, zero is accepted (non-negative)
        strict: If True, only accepts int/float (explicitly rejects bool, Decimal, etc.)

    Returns:
        The validated number (int or float)

    Raises:
        ContractError: If value is not a number, negative, or zero when not allowed
    """
    prefix = f"Arg '{description}'" if description else "Value"

    # 1. Type check
    if strict:
        if not (isinstance(candidate, (int, float)) and not isinstance(candidate, bool)):
            _fail(
                message=f"{prefix} must be an int or float (bool not allowed in strict mode)",
                Description=description or "Unnamed",
                Received_type=type(candidate).__name__,
            )
    else:
        # Permissive mode: accept anything that is int or float (bool still accepted)
        if not isinstance(candidate, (int, float)):
            _fail(
                message=f"{prefix} must be a number",
                Description=description or "Unnamed",
                Received_type=type(candidate).__name__,
            )

    # 2. Value check - unified base message
    if candidate < 0:
        _fail(
            message=f"{prefix} must be positive",
            Description=description or "Unnamed",
            Received=candidate,
        )

    if candidate == 0 and not allow_zero:
        _fail(
            message=f"{prefix} must be positive (greater than zero)",
            Description=description or "Unnamed",
            Received=candidate,
        )

    return candidate

# region bool

def ensure_true(condition: bool, description: str = "") -> None:
    """Ensures that the provided condition is strictly True."""
    _ensure_bool_strict(condition, expected=True, description=description)


def ensure_false(condition: bool, description: str = "") -> None:
    """Ensures that the provided condition is strictly False."""
    _ensure_bool_strict(condition, expected=False, description=description)


def _ensure_bool_strict(condition: bool, expected: bool, description: str = "", ) -> None:
    if not (isinstance(condition, bool) and condition is expected):
        expected_str = "True" if expected else "False"
        message = (
            f"Assertion failed: {description}"
            if description
            else f"Condition must be {expected_str}"
        )
        _fail(
            message=message,
            Description=description or None,
            Received=repr(condition),
            Received_Type=type(condition).__name__,
        )


# endregion


# region str
def ensure_str_is_valued(candidate: Any, description: str | None = None) -> None:
    """
    Ensures that the candidate is not None or an empty string, raising a ContractError if it is.
    """
    ensure_not_none(candidate, description)
    ensure_type(candidate, str, description)

    if not candidate.strip():
        prefix = f"Arg '{description}'" if description else "Value"
        _fail(
            message=f"{prefix} cannot be an empty string",
            Description=description or "Unnamed",
            Received="Empty String",
        )


def ensure_str_exact_length(candidate: Any, exact_length: int, description: str | None = None) -> str:
    """Ensures string has exactly exact_length characters."""
    ensure_type(candidate, str, description)
    return _ensure_length(candidate, exact_length=exact_length, description=description)


def ensure_str_min_length(candidate: Any, min_length: int, description: str | None = None) -> str:
    ensure_type(candidate, str, description)
    return _ensure_length(candidate, min_length=min_length, description=description)


def ensure_str_max_length(candidate: Any, max_length: int, description: str | None = None) -> str:
    """Ensures string has at most min_length characters."""
    ensure_type(candidate, str, description)
    return _ensure_length(candidate, max_length=max_length, description=description)


def ensure_str_length_between(
        candidate: Any,
        min_length: int,
        max_length: int,
        description: str | None = None,
) -> str:
    ensure_type(candidate, str, description)
    return _ensure_length(
        candidate,
        min_length=min_length,
        max_length=max_length,
        description=description,
    )


# endregion

# region internal

def _fail(message: str, **context: Any) -> NoReturn:
    """Central point of truth for all guard failures."""
    raise ContractError(
        create_clean_error_context(
            description=message,
            object_info=context or None,
            frames_to_show=3,
            skip_patterns=None,
        )
    )


def _ensure_length(
        value: Any,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        exact_length: int | None = None,
        description: str | None = None,
) -> Any:
    """
    Internal helper: Enforce length constraints on any object that supports len().

    This is NOT part of the public API.
    Use the specific convenience functions instead (ensure_str_min_length, etc.).

    Raises ContractError if any length constraint is violated.
    Returns the original value when all checks pass.
    """
    actual_length = len(value)

    prefix = f"Arg '{description}'" if description else "Value"

    if exact_length is not None:
        if actual_length != exact_length:
            _fail(
                message=f"{prefix} must have an exact length of {exact_length}",
                Description=description or "Unnamed",
                Expected_length=exact_length,
                Actual_length=actual_length,
                Value=repr(value)[:100],  # truncate very long values
            )
    else:
        if min_length is not None and actual_length < min_length:
            _fail(
                message=f"{prefix} must have a minimum length of {min_length}",
                Description=description or "Unnamed",
                Min_length=min_length,
                Actual_length=actual_length,
                Value=repr(value)[:100],
            )

        if max_length is not None and actual_length > max_length:
            _fail(
                message=f"{prefix} must have a maximum length of {max_length}",
                Description=description or "Unnamed",
                Max_length=max_length,
                Actual_length=actual_length,
                Value=repr(value)[:100],
            )

    return value


# Later, if and when needed:
# def ensure_list_min_length(candidate: Any, min_length: int, description: str | None = None) -> list:
#     ensure_type(candidate, list, description)
#     return _ensure_length(candidate, min_length=min_length, description=description)
#
#
# def ensure_bytes_exact_length(candidate: Any, exact_length: int, description: str | None = None) -> bytes:
#     ensure_type(candidate, bytes, description)
#     return _ensure_length(candidate, exact_length=exact_length, description=description, )


# endregion


# region custom error
class ContractError(AssertionError):
    """Raised when a programming contract is violated in our own code."""


def create_clean_error_context(
        description: str,
        object_info: dict[str, Any] | None,
        frames_to_show: int = 3,
        skip_patterns: list[str] | None = None,
) -> str:
    """
    Creates a clean, formatted error context with filtered traceback.
    """
    object_info = object_info or {}
    skip_patterns = skip_patterns or ['pytest', 'pluggy', '_pytest', 'site-packages']

    stack = traceback.extract_stack()
    relevant_frames = [frame for frame in stack if not any(skip in frame.filename.lower() for skip in skip_patterns)]

    clean_traceback = ''.join(traceback.format_list(relevant_frames[-(frames_to_show or 3):]))

    error_parts = [description]
    if object_info:
        error_parts.extend(f"{key}: {value}" for key, value in object_info.items())

    error_parts.append("\nRelevant call stack:")
    error_parts.append(clean_traceback)

    return "\n".join(error_parts)

# endregion
