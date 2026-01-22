"""
Order type enumeration for trade execution.
"""

from enum import StrEnum, auto


class OrderType(StrEnum):
    """
    Type of order for trade execution.
    
    Attributes:
        LMT: Limit order - execute at specified price or better
        MKT: Market order - execute at current market price
        STOP_LOSS: Stop order - becomes market order when stop price reached
        STOP_LIMIT: Stop limit - becomes limit order when stop price reached
    
    Usage:
        ```python
        order = OrderType.LMT
        assert order == "LMT"
        assert order.is_limit
        
        market = OrderType.MKT
        assert market.is_market
        ```
    """
    LMT = auto()
    MKT = auto()
    STOP_LOSS = auto()
    STOP_LIMIT = auto()
    
    @property
    def is_limit(self) -> bool:
        """True if this is a limit order (LMT or STOP_LIMIT)."""
        return self in (OrderType.LMT, OrderType.STOP_LIMIT)
    
    @property
    def is_market(self) -> bool:
        """True if this is a market order (MKT or STOP)."""
        return self in (OrderType.MKT, OrderType.STOP_LOSS)

    # Option 1 - Most readable + maintainable (recommended)
    def __str__(self) -> str:
        match self:
            case OrderType.LMT | OrderType.MKT:
                return self.value  # or self.name if you prefer
            case OrderType.STOP_LOSS | OrderType.STOP_LIMIT:
                return self.name.replace("_", " ").title()
            case _:
                raise ValueError(f"Unknown order type: {self}")