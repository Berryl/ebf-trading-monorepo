"""
Ticker symbol value object.
"""

from dataclasses import dataclass

from ebf_core.guards import guards as g


@dataclass(frozen=True)
class Ticker:
    """
    Represents an underlying security ticker symbol.
    
    Ticker symbols are normalized to uppercase and validated for format.
    
    Attributes:
        symbol: The ticker symbol (e.g., 'IBM', 'HOG', 'SPY')
    
    Usage:
        ```python
        ticker = Ticker('IBM')
        assert ticker.symbol == 'IBM'
        
        # Case normalization
        ticker2 = Ticker('hog')
        assert ticker2.symbol == 'HOG'
        
        # Equality
        assert Ticker('IBM') == Ticker('ibm')
        ```
    """
    symbol: str
    
    def __post_init__(self):
        g.ensure_str_is_valued(self.symbol, 'symbol')
        g.ensure_str_max_length(self.symbol, 10, 'symbol')
        
        # Normalize to uppercase
        normalized = self.symbol.upper().strip()
        object.__setattr__(self, 'symbol', normalized)
        
        # Validate the format (letters only, with optional . or -)
        if not all(c.isalpha() or c in '.-' for c in normalized):
            raise ValueError(
                f"Ticker symbol '{self.symbol}' must contain only letters, dots, or hyphens"
            )
    
    def __str__(self) -> str:
        """String representation: 'IBM'"""
        return self.symbol
    
    def __repr__(self) -> str:
        """Developer representation: Ticker('IBM')"""
        return f"Ticker('{self.symbol}')"
