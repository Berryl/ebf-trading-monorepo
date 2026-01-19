"""
Contract quantity value object.
"""

from dataclasses import dataclass
from ebf_core.guards import guards as g


@dataclass(frozen=True)
class ContractQuantity:
    """
    Represents the number of option contracts in a position.
    
    Each option contract typically represents 100 shares of the underlying.
    Quantity must be a positive integer.
    
    Attributes:
        contracts: Number of contracts (must be positive)
    
    Usage:
        ```python
        qty = ContractQuantity(10)
        assert qty.contracts == 10
        assert qty.shares_represented == 1000
        
        # Arithmetic
        doubled = qty * 2
        assert doubled.contracts == 20
        ```
    """
    contracts: int
    
    def __post_init__(self):
        g.ensure_type(self.contracts, expected_type=int, description="Contract quantity")
        g.ensure_positive_number(self.contracts, description="Contract quantity", strict=True)

    @property
    def shares_represented(self) -> int:
        """
        Calculate the number of shares represented by these contracts.
        
        Standard option contracts represent 100 shares each.
        
        Returns:
            Number of shares (contracts * 100)
        """
        return self.contracts * 100
    
    def __str__(self) -> str:
        """String representation: '10'"""
        return str(self.contracts)
    
    def __repr__(self) -> str:
        """Developer representation: ContractQuantity(10)"""
        return f"ContractQuantity({self.contracts})"
    
    # region Arithmetic operations
    def __mul__(self, scalar: int) -> 'ContractQuantity':
        """Multiply contract quantity by a scalar."""
        if not isinstance(scalar, int):
            return NotImplemented
        return ContractQuantity(self.contracts * scalar)
    
    def __rmul__(self, scalar: int) -> 'ContractQuantity':
        """Support scalar * quantity."""
        return self.__mul__(scalar)
    
    def __add__(self, other: 'ContractQuantity') -> 'ContractQuantity':
        """Add two contract quantities."""
        if not isinstance(other, ContractQuantity):
            return NotImplemented
        return ContractQuantity(self.contracts + other.contracts)
    
    # Comparison operators
    def __lt__(self, other: 'ContractQuantity') -> bool:
        if not isinstance(other, ContractQuantity):
            return NotImplemented
        return self.contracts < other.contracts
    
    def __le__(self, other: 'ContractQuantity') -> bool:
        if not isinstance(other, ContractQuantity):
            return NotImplemented
        return self.contracts <= other.contracts
    
    def __gt__(self, other: 'ContractQuantity') -> bool:
        if not isinstance(other, ContractQuantity):
            return NotImplemented
        return self.contracts > other.contracts
    
    def __ge__(self, other: 'ContractQuantity') -> bool:
        if not isinstance(other, ContractQuantity):
            return NotImplemented
        return self.contracts >= other.contracts
    # endregion
