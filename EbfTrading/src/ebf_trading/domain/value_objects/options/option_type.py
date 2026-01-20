"""
Option type enumeration (CALL or PUT).
"""

from enum import StrEnum, auto


class OptionType(StrEnum):
    """
    Type of option contract.
    
    Attributes:
        CALL: Right to buy the underlying at the strike price if LONG,
                or the obligation to sell the underlying at the strike price if SHORT
        PUT: Right to sell the underlying at the strike price if LONG
                or the obligation to buy the underlying at the strike price if SHORT
    
    Usage:
        ```python
        opt_type = OptionType.CALL
        assert opt_type == "CALL"
        assert opt_type.is_call
        
        put = OptionType.PUT
        assert put.is_put
        ```
    """
    CALL = auto()
    PUT = auto()
    
    @property
    def is_call(self) -> bool:
        """True if this is a CALL option."""
        return self == OptionType.CALL
    
    @property
    def is_put(self) -> bool:
        """True if this is a PUT option."""
        return self == OptionType.PUT
    
    def __str__(self) -> str:
        """String representation."""
        return self.value

    def to_occ_format(self) -> str:
         return self.__str__()[0].upper()
