from datetime import datetime
from decimal import Decimal
from enum import StrEnum, auto

from ebf_core.guards import guards as g

from ebf_trading.domain.value_objects.options.option import Option
from ebf_trading.domain.value_objects.options.option_type import OptionType
from ebf_trading.domain.value_objects.options.strike import Strike


class OptionFormat(StrEnum):
    OCC = auto()  # industry standard OSI 21 char symbol inl 6 chars padded as needed ('IBM   ')
    OCC_SANS_PADDING = auto()  # same as OCC without padding ('IBM')


def to_underlying_str(o: Option, fnt: OptionFormat = OptionFormat.OCC) -> str:
    match fnt:
        case OptionFormat.OCC:
            return o.underlying.symbol.ljust(6)
        case OptionFormat.OCC_SANS_PADDING:
            return o.underlying.symbol
        case _:
            raise ValueError(f"Unknown format: {fnt}")


def from_underlying_str(s: str, fnt: OptionFormat = OptionFormat.OCC) -> str:
    match fnt:
        case OptionFormat.OCC:
            g.ensure_str_exact_length(s, 6, "underlying symbol")
        case OptionFormat.OCC_SANS_PADDING:
            g.ensure_str_max_length(s, 6, "underlying symbol")
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
        raise ValueError(f"Invalid expiration date in OCC symbol: {s}") from e


def to_contract_type_str(o: Option, fnt: OptionFormat = OptionFormat.OCC) -> str:
    match fnt:
        case OptionFormat.OCC | OptionFormat.OCC_SANS_PADDING:
            return 'C' if o.is_call else 'P'
        case _:
            raise ValueError(f"Unknown format: {fnt}")


def from_contract_type(s: str, fnt: OptionFormat = OptionFormat.OCC) -> OptionType:
    match fnt:
        case OptionFormat.OCC | OptionFormat.OCC_SANS_PADDING:
            g.ensure_str_exact_length(s, 1, "contract type")
        case _:
            raise ValueError(f"Unknown format: {fnt}")

    if s not in ('C', 'P'):
        raise ValueError(f"Invalid option type in OCC symbol: {s} (must be C or P)")
    return OptionType.CALL if s == 'C' else OptionType.PUT


def to_strike_str(o: Option, fnt: OptionFormat = OptionFormat.OCC) -> str:
    match fnt:
        case OptionFormat.OCC | OptionFormat.OCC_SANS_PADDING:
            # Strike (8 digits: whole dollars + cents, e.g., 00042500 for $42.50)
            # Multiply by 1000 to get millidollars, then format as 8 digits
            strike_millidollars = int(o.strike.price.amount * 1000)
            return f"{strike_millidollars:08d}"
        case _:
            raise ValueError(f"Unknown format: {fnt}")

def from_strike(s: str, fnt: OptionFormat = OptionFormat.OCC) -> Strike:
    match fnt:
        case OptionFormat.OCC | OptionFormat.OCC_SANS_PADDING:
            g.ensure_str_exact_length(s, 8, "strike")
        case _:
            raise ValueError(f"Unknown format: {fnt}")

    try:
        strike_millidollars = int(s)
        strike_amount = Decimal(strike_millidollars) / 1000
        return Strike.from_amount(float(strike_amount))
    except (ValueError, IndexError) as e:
        raise ValueError(f"Invalid strike price in OCC symbol: {s}") from e

