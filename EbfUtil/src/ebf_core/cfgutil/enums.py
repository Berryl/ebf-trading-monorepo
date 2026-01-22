from enum import Enum
from typing import TypeVar, Type, overload
from ebf_core.guards import guards as g


E = TypeVar("E", bound=Enum)


def enum_from_str(value: str | None, enum_type: Type[E]) -> E:
    """
    Convert a string (case-insensitive, hyphens → underscores) to an Enum member.

    """
    g.ensure_str_is_valued(value, "value")

    normalized = str(value).strip().replace("-", "_").replace(" ", "_").upper()

    try:
        return enum_type[normalized]
    except KeyError as exc:
        valid = ", ".join(m.name for m in enum_type)
        raise ValueError(
            f"'{value}' is not a valid {enum_type.__name__}. "
            f"Valid options: {valid}"
        ) from exc


@overload
def normalize_enum_fields(data: dict, field: str, enum_type: Type[E]) -> dict: ...


@overload
def normalize_enum_fields(data: dict, fields: list[str], enum_type: Type[E]) -> dict: ...


def normalize_enum_fields(data: dict, field: str | list[str], enum_type: Type[E], ) -> dict:
    """
    Normalize one or more enum-bearing fields in a config dict.
    Mutates the dict in-place and returns it for convenience.
    """
    data = dict(data)  # shallow copy
    fields = [field] if isinstance(field, str) else field

    for f in fields:
        if f in data:
            data[f] = enum_from_str(data[f], enum_type)

    return data