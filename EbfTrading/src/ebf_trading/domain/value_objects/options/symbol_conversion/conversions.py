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


def to_expiration_str(o: Option, fnt: OptionFormat = OptionFormat.OCC) -> str:
    # Expiration (YYMMDD)
    match fnt:
        case OptionFormat.OCC | OptionFormat.OCC_SANS_PADDING:
            return o.expiration.strftime('%y%m%d')
        case _:
            raise ValueError(f"Unknown format: {fnt}")


def from_expiration(s: str, fnt: OptionFormat = OptionFormat.OCC) -> datetime:
    match fnt:
        case OptionFormat.OCC | OptionFormat.OCC_SANS_PADDING:
            g.ensure_str_exact_length(s, 6, "expiration date")
        case _:
            raise ValueError(f"Unknown format: {fnt}")
    try:
        year = int(s[0:2]) + 2000  # YY -> YYYY
        month = int(s[2:4])
        day = int(s[4:6])
        return datetime(year, month, day)
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid expiration date in OCC ticker: {s}") from e
