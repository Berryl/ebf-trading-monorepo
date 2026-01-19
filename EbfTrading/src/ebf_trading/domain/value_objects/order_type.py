"""
Order type enumeration for trade execution.
"""

from enum import StrEnum


class OrderType(StrEnum):
    """
    Type of order for trade execution.
    
    Attributes:
        LMT: Limit order - execute at specified price or better
        MKT: Market order - execute at current market price
        STOP: Stop order - becomes market order when stop price reached
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
    LMT = "LMT"
    MKT = "MKT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    
    @property
    def is_limit(self) -> bool:
        """True if this is a limit order (LMT or STOP_LIMIT)."""
        return self in (OrderType.LMT, OrderType.STOP_LIMIT)
    
    @property
    def is_market(self) -> bool:
        """True if this is a market order (MKT or STOP)."""
        return self in (OrderType.MKT, OrderType.STOP)
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
