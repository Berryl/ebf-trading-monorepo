from enum import StrEnum, auto

from ebf_core.guards import guards as g
from ebf_trading.domain.value_objects.options.option import Option


class OptionFormat(StrEnum):
    OCC = auto() # industry standard OSI 21 char symbol inl 6 chars padded as needed ('IBM   ')
    OCC_SANS_PADDING = auto() # same as OCC without padding ('IBM')

def to_underlying_str(o: Option, fnt: OptionFormat = OptionFormat.OCC) -> str:
    match fnt:
        case OptionFormat.OCC:
            return o.underlying.symbol.ljust(6)
        case OptionFormat.OCC_SANS_PADDING:
            return o.underlying.symbol.ljust(6)
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
