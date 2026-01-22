"""
Position direction enumeration (LONG or SHORT).
"""

from enum import StrEnum, auto
from typing import Self


class Direction(StrEnum):
    """
    Direction of a position (long or short).
    
    Attributes:
        LONG: Buying to open or holding a long position
        SHORT: Selling to open or holding a short position
    
    Usage:
        ```python
        direction = Direction.LONG
        assert direction == "LONG"
        assert direction.is_long
        
        short = Direction.SHORT
        assert short.is_short
        ```
    """
    LONG = auto()
    SHORT = auto()
    
    @property
    def is_long(self) -> bool:
        """True if this is a LONG position."""
        return self == Direction.LONG
    
    @property
    def is_short(self) -> bool:
        """True if this is a SHORT position."""
        return self == Direction.SHORT
    
    def opposite(self) -> Self:
        """
        Get the opposite direction.
        
        Returns:
            SHORT if LONG, LONG if SHORT
            
        Example:
            ```python
            long = Direction.LONG
            assert long.opposite() == Direction.SHORT
            ```
        """
        return Direction.SHORT if self.is_long else Direction.LONG
    
    def __str__(self) -> str:
        """String representation."""
        return self.value
