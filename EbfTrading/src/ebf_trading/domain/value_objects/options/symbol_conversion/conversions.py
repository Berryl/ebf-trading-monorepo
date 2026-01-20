from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto

from ebf_core.guards import guards as g

from ebf_trading.domain.value_objects.options.option import Option
from ebf_trading.domain.value_objects.options.option_type import OptionType
from ebf_trading.domain.value_objects.options.strike import Strike


class OptionFormat(StrEnum):
    OCC = auto()  # industry standard OSI 21 char ticker inl 6 chars padded as needed ('IBM   ')
    OCC_SANS_PADDING = auto()  # same as OCC without padding ('IBM')


def to_underlying_str(o: Option, fnt: OptionFormat = OptionFormat.OCC) -> str:
    match fnt:
        case OptionFormat.OCC:
            return o.underlying.ticker.ljust(6)
        case OptionFormat.OCC_SANS_PADDING:
            return o.underlying.ticker
        case _:
            raise ValueError(f"Unknown format: {fnt}")


def from_underlying_str(s: str, fnt: OptionFormat = OptionFormat.OCC) -> str:
    match fnt:
        case OptionFormat.OCC:
            g.ensure_str_exact_length(s, 6, "underlying ticker")
        case OptionFormat.OCC_SANS_PADDING:
            g.ensure_str_max_length(s, 6, "underlying ticker")
        case _:
            raise ValueError(f"Unknown format: {fnt}")

    return s.strip().upper()
