import traceback
from collections.abc import Iterable
from pathlib import Path
from typing import Any, TypeVar, NoReturn

from typeguard import (
    CollectionCheckStrategy,
    ForwardRefPolicy,
    TypeCheckError,
    check_type,
)


# region helpers
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


# endregion


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


def ensure_not_empty_str(candidate: Any, description: str | None = None) -> None:
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


T = TypeVar('T')


def ensure_type(candidate: Any, expected_type: type[T], description: str | None = None, ) -> T:
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
        expected_name = getattr(expected_type, "__name__", str(expected_type))

        if hasattr(expected_type, "__origin__"):
            # Generic like list[int] → use typeguard's message
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
        ensure_not_empty_str(candidate, description)
        return Path(candidate)

    prefix = f"Arg '{description}'" if description else "Value"
    _fail(
        message=f"{prefix} must be a Path or non-empty string",
        Description=description or "Unnamed",
        **{"Received Type": type(candidate).__name__},
    )


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


def ensure_true(condition: bool, description: str = "") -> None:
    """Ensures that the provided condition is strictly True."""
    _ensure_bool_strict(condition, expected=True, description=description)


def ensure_false(condition: bool, description: str = "") -> None:
    """Ensures that the provided condition is strictly False."""
    _ensure_bool_strict(condition, expected=False, description=description)
