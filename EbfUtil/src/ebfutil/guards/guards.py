import traceback
from collections.abc import Iterable
from typing import Any, TypeVar, Type, Optional

from typeguard import check_type, ForwardRefPolicy, CollectionCheckStrategy, TypeCheckError


def ensure_not_none(candidate: Any, description: str | None = None) -> None:
    """
    Ensures that the candidate is not None, raising an AssertionError if it is.
    """
    if candidate is None:
        prefix = f"Arg '{description}'" if description else "Value"

        object_info = {
            "Description": description or "Unnamed",
            "Received": "None"
        }

        raise AssertionError(create_clean_error_context(
            description=f"{prefix} cannot be None",
            object_info=object_info
        ))


def ensure_not_empty_str(candidate: Any, description: str | None = None) -> None:
    """
    Ensures that the candidate is not None or an empty string, raising an AssertionError if it is.
    """
    ensure_not_none(candidate, description)
    ensure_type(candidate, str, description)

    if not candidate.strip():
        prefix = f"Arg '{description}'" if description else "Value"

        object_info = {
            "Description": description or "Unnamed",
            "Received": "Empty String"
        }

        raise AssertionError(create_clean_error_context(
            description=f"{prefix} cannot be an empty string",
            object_info=object_info
        ))


T = TypeVar('T')


def ensure_type(candidate: Any, expected_type: Type[T], description: str | None = None) -> T:
    """
    Ensures that the candidate is of the expected type, raising an AssertionError if not.
    """
    try:
        check_type(value=candidate,
                   expected_type=expected_type,
                   forward_ref_policy=ForwardRefPolicy.ERROR,
                   collection_check_strategy=CollectionCheckStrategy.ALL_ITEMS)
        return candidate
    except TypeCheckError as e:
        actual_type = type(candidate).__name__ if candidate is not None else "None"
        prefix = f"Arg '{description}'" if description else "Value"
        expected_name = getattr(expected_type, '__name__', str(expected_type))

        message = (f"{prefix} must be of type {expected_name} "
                   f"(it was type {actual_type})") \
            if not hasattr(expected_type, '__origin__') else f"{prefix}: {e} (it was type {actual_type})"

        raise AssertionError(create_clean_error_context(
            description=message,
            object_info={"Description": description or "Unnamed",
                         "Expected Type": expected_name, "Received Type": actual_type},
            frames_to_show=3
        )) from e


def ensure_attribute(candidate: Any, attr_spec: str, description: str | None = None) -> T:
    """
    Ensures that the candidate has the specified attribute.
    """
    ensure_not_none(candidate, description)

    if not hasattr(candidate, attr_spec):
        description = description or f"{type(candidate).__name__} has no attribute '{attr_spec}'"

        available_attrs = sorted(dir(candidate))
        attr_list = ", ".join(available_attrs[:10])
        if len(available_attrs) > 10:
            attr_list += "..."

        object_info = {
            "Object type": type(candidate).__name__,
            "Requested attribute": attr_spec,
            "Available attributes": attr_list
        }

        raise AttributeError(create_clean_error_context(description, object_info))

    return candidate

def ensure_in(candidate: Any, choices: Iterable, description: str | None = None) -> None:
    """
    Ensures that the candidate is a member of the provided choices.
    """
    ensure_not_none(choices, "choices")

    try:
        if candidate in choices:
            return
    except TypeError:
        try:
            for item in choices:
                if candidate == item:
                    return
        except TypeError:
            pass  # Non-iterable 'choices' — will fall through to error

    shown_items: list[Any] = []
    try:
        it = iter(choices)
        for _ in range(10):
            shown_items.append(next(it))
    except Exception:   # noqa PyBroadException
        pass

    shown = ", ".join(repr(x) for x in shown_items)
    try:
        if len(choices) > len(shown_items):  # type: ignore[arg-type]
            shown = (shown + ", ...") if shown else "..."
    except Exception:  # noqa PyBroadException
        pass

    prefix = f"Arg '{description}'" if description else "Value"
    raise AssertionError(create_clean_error_context(
        description=f"{prefix} must be one of the allowed choices",
        object_info={
            "Description": description or "Unnamed",
            "Received": repr(candidate),
            "Allowed (sample)": shown if shown else "(unavailable)"
        }
    ))

def create_clean_error_context(
        description: str,
        object_info: Optional[dict] = None,
        skip_patterns: Optional[list[str]] = None,
        frames_to_show: int = 3
) -> str:
    """
    Creates a clean, formatted error context with filtered traceback.
    """
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
