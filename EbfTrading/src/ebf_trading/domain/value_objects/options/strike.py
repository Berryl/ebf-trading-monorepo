"""
Strike price value object.
"""

from dataclasses import dataclass
from typing import Self

from ebf_domain.money.money import Money
from ebf_domain.money.currency import USD
from ebf_core.guards import guards as g


@dataclass(frozen=True)
class Strike:
    """
    Represents an option strike-price.
    
    Strike prices must be positive and use Money for type safety.
    
    Attributes:
        price: The strike price as Money
    
    Usage:
        ```python
        strike = Strike(Money.mint(42.50, USD))
        assert strike.price.amount == Decimal('42.50')
        
        # Convenience factory
        strike2 = Strike.from_amount(42.50)
        assert strike2.price.amount == Decimal('42.50')
        
        # Comparison
        low = Strike.from_amount(40.00)
        high = Strike.from_amount(45.00)
        assert low < high
        ```
    """
    price: Money
    
    def __post_init__(self):
        g.ensure_positive_number(self.price.amount, description="Strike price")

    @classmethod
    def from_amount(cls, amount: float | int, currency=USD) -> Self:
        """
        Create a Strike from a numeric amount.
        
        Args:
            amount: The strike price as a number
            currency: Currency for the strike (default: USD)
            
        Returns:
            New Strike instance
            
        Example:
            ```python
            strike = Strike.from_amount(42.50)
            strike_eur = Strike.from_amount(100, EUR)
            ```
        """
        return cls(Money.mint(amount, currency))
    
    def __str__(self) -> str:
        """String representation: '$42.50'"""
        return str(self.price)
    
    def __repr__(self) -> str:
        """Developer representation."""
        return f"Strike({self.price!r})"
    
    # Comparison operators for strike ordering
    def __lt__(self, other: Self) -> bool:
        g.ensure_type(other, Strike, description="Comparison with other Strike")
        return self.price < other.price

    def __le__(self, other: Self) -> bool:
        g.ensure_type(other, Strike, description="Comparison with other Strike")
        return self.price <= other.price

    def __gt__(self, other: Self) -> bool:
        g.ensure_type(other, Strike, description="Comparison with other Strike")
        return self.price > other.price

    def __ge__(self, other: Self) -> bool:
        g.ensure_type(other, Strike, description="Comparison with other Strike")
        return self.price >= other.price
