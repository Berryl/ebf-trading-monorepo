from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Self

from ebf_domain.money.currency import Currency, USD


@dataclass(frozen=True)
class Money:
    """
    Money represents a monetary amount with a specific currency.
    
    Stores amount as integer cents/subunits for efficiency and precision.
    All arithmetic operations use Decimal for precision, then convert back to int.
    
    Attributes:
        amount_cents: Amount in currency's subunits (e.g., cents for USD)
        currency: Currency instance defining the money's type
    
    Usage:
        ```python
        # Create money from decimal amount
        price = Money.mint(29.99, USD) # $29.99
        
        # Create from cents (from DB/API)
        db_value = Money.from_cents(2999, USD) # $29.99
        
        # Arithmetic
        total = price + tax
        discount = price * Decimal("0.10")
        per_person = bill / 4
        
        # Get decimal amount
        print(price.amount) # Decimal('29.99')
        
        # Format for display
        print(price) # $29.99
        ```
    
    Design Decisions:
        - Integer storage: Efficient, database-friendly, no Decimal serialization
        - Decimal arithmetic: Precise calculations, proper rounding
        - Frozen dataclass: Immutable, hashable, thread-safe
        - Currency enforcement: Operations require matching currencies
    """
    amount_cents: int
    currency: Currency

    # region Factory Methods

    @classmethod
    def mint(cls, amount: object, currency: Currency = USD) -> Self:
        """
        Create Money from a decimal amount.
        
        Converts amount to currency's subunits with proper rounding.
        
        Args:
            amount: Decimal amount (e.g., 29.99 for $29.99)
            currency: Currency instance (default: USD)
            
        Returns:
            New Money instance
            
        Example:
            ```python
            price = Money.mint(29.99, USD)
            tax = Money.mint(2.40, USD)
            ```
        """
        dec_amount = Decimal(str(amount))
        cents = (dec_amount * currency.sub_units_per_unit).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return cls(int(cents), currency)

    @classmethod
    def zero(cls, currency: Currency = USD) -> Self:
        """
        Create zero money value.
        
        Args:
            currency: Currency instance (default: USD)
            
        Returns:
            Money with zero amount
        """
        return cls(0, currency)

    @classmethod
    def from_cents(cls, cents: int, currency: Currency = USD) -> Self:
        """
        Create Money from integer subunits (cents).
        
        Useful for database storage and API interactions.
        
        Args:
            cents: Amount in subunits (e.g., 2999 for $29.99)
            currency: Currency instance (default: USD)
            
        Returns:
            New Money instance
            
        Example:
            ```python
            # From a database
            db_amount = 2999
            price = Money.from_cents(db_amount, USD)
            
            # From API response
            api_cents = response['amount_cents']
            money = Money.from_cents(api_cents, USD)
            ```
        """
        return cls(cents, currency)

    # Legacy alias for backward compatibility
    @classmethod
    def from_db(cls, amount: int, currency: Currency = USD) -> Self:
        """Legacy alias for from_cents()."""
        return cls.from_cents(amount, currency)

    # endregion

    # region Properties

    @property
    def amount(self) -> Decimal:
        """
        Get amount as Decimal for display and calculation.
        
        Returns:
            Decimal amount (e.g., Decimal('29.99') for $29.99)
        """
        q = Decimal(1).scaleb(-self.currency.sub_unit_precision)  # 10 ** -precision
        return (Decimal(self.amount_cents) / self.currency.sub_units_per_unit).quantize(q)

    @property
    def dollars_part(self) -> int:
        """
        Get the major unit part (dollars for USD).

        Returns:
            Whole unit amount (truncates toward zero for negatives)

        Example:
            ```python
            money = Money.mint(29.99, USD)
            assert money.dollars_part == 29

            #noinspection GrazieInspection
            negative = Money.mint(-29.99, USD)
            assert negative.dollars_part == -29 # Truncates toward zero
            ```
        """
        # Truncate toward zero (not floor division which rounds down)
        # For positive: 2999 // 100 = 29 ✓
        # For negative: -2999 // 100 = -30 ✗ (floor division)
        # Solution: sign * (abs(cents) // sub_units)
        sign = 1 if self.amount_cents >= 0 else -1
        return sign * (abs(self.amount_cents) // self.currency.sub_units_per_unit)

    @property
    def cents_part(self) -> int:
        """
        Get the minor unit part (cents for USD).
        
        Returns:
            Sub-unit amount (always positive)
            
        Example:
            ```python
            money = Money.mint(29.99, USD)
            assert money.cents_part == 99
            
            #noinspection GrazieInspection
            negative = Money.mint(-29.99, USD)
            assert negative.cents_part == 99 # Absolute value
            ```
        """
        # Get absolute cents value: abs(amount_cents) % sub_units
        return abs(self.amount_cents) % self.currency.sub_units_per_unit

    @property
    def is_zero(self) -> bool:
        """True if the amount is zero."""
        return self.amount_cents == 0

    @property
    def is_positive(self) -> bool:
        """True if the amount is positive (> 0)."""
        return self.amount_cents > 0

    @property
    def is_negative(self) -> bool:
        """True if the amount is negative (< 0)."""
        return self.amount_cents < 0

    # endregion

    # region Arithmetic Operations

    def __add__(self, other: object) -> Self:
        """
        Add two Money objects (same currency required).
        
        Special case: Allows adding 0 to support sum() function.
        """
        if other == 0:
            # Allows sum([money1, money2, money3]) to work
            return self

        if not isinstance(other, Money):
            return NotImplemented

        self._validate_same_currency(other, action='add')

        # Direct integer addition - very efficient
        return Money.from_cents(
            self.amount_cents + other.amount_cents,
            self.currency
        )

    def __radd__(self, other: object) -> Self:
        """Support sum([money1, money2]) by handling 0 + money."""
        return self.__add__(other)

    def __sub__(self, other: object) -> Self:
        """Subtract two Money objects (same currency required)."""
        if not isinstance(other, Money):
            return NotImplemented

        self._validate_same_currency(other, action='subtract')

        return Money.from_cents(
            self.amount_cents - other.amount_cents,
            self.currency
        )

    def __rsub__(self, other: object) -> Self:
        """Support other - money."""
        return (-self).__add__(other)

    def __mul__(self, scalar: object) -> Self:
        """
        Multiply money by a scalar value.
        
        Args:
            scalar: Number to multiply by (int, float, or Decimal)
            
        Raises:
            TypeError: If scalar is Money (cannot multiply Money by Money)
        """
        if isinstance(scalar, Money):
            raise TypeError("Cannot multiply Money by Money (use scalar values)")

        # Use Decimal for precision, then round to integer cents
        result_cents = (Decimal(self.amount_cents) * Decimal(str(scalar))).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        )
        return Money.from_cents(int(result_cents), self.currency)

    def __rmul__(self, scalar: object) -> Self:
        """Support scalar * Money (e.g., 2 * price)."""
        return self.__mul__(scalar)

    def __truediv__(self, scalar: object) -> Self:
        """
        Divide money by a scalar value.
        
        Args:
            scalar: Number to divide by (int, float, or Decimal)
            
        Raises:
            TypeError: If scalar is Money (cannot divide Money by Money)
            ZeroDivisionError: If scalar is zero
        """
        if isinstance(scalar, Money):
            raise TypeError("Cannot divide Money by Money (use scalar values)")

        if scalar == 0:
            raise ZeroDivisionError("Cannot divide money by zero")

        result_cents = (Decimal(self.amount_cents) / Decimal(str(scalar))).quantize(
            Decimal('1'), rounding=ROUND_HALF_UP
        )
        return Money.from_cents(int(result_cents), self.currency)

    def __floordiv__(self, scalar: object) -> Self:
        """Floor division of money by scalar."""
        if isinstance(scalar, Money):
            raise TypeError("Cannot divide Money by Money (use scalar values)")
        if not isinstance(scalar, int):
            raise TypeError("Floor division requires an int scalar")

        if scalar == 0:
            raise ZeroDivisionError("Cannot divide money by zero")

        result_cents = self.amount_cents // int(scalar)
        return Money.from_cents(result_cents, self.currency)

    def __neg__(self) -> Self:
        """Negate money amount."""
        return Money.from_cents(-self.amount_cents, self.currency)

    def __abs__(self) -> Self:
        """Absolute value of money."""
        return Money.from_cents(abs(self.amount_cents), self.currency)

    # endregion

    # region Comparison Operations

    def __eq__(self, other: object) -> bool:
        """Check equality (amount and currency must match)."""
        if not isinstance(other, Money):
            return False
        return (self.currency == other.currency and
                self.amount_cents == other.amount_cents)

    def __lt__(self, other: object) -> bool:
        """Less than comparison (same currency required)."""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_same_currency(other)
        return self.amount_cents < other.amount_cents

    def __le__(self, other: object) -> bool:
        """Less than or equal comparison (same currency required)."""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_same_currency(other)
        return self.amount_cents <= other.amount_cents

    def __gt__(self, other: object) -> bool:
        """Greater than comparison (same currency required)."""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_same_currency(other)
        return self.amount_cents > other.amount_cents

    def __ge__(self, other: object) -> bool:
        """Greater than or equal comparison (same currency required)."""
        if not isinstance(other, Money):
            return NotImplemented
        self._validate_same_currency(other)
        return self.amount_cents >= other.amount_cents

    def _validate_same_currency(self, other: Money, action: str = 'compare') -> None:
        """Ensure two Money objects have the same currency."""
        if self.currency != other.currency:
            raise TypeError(
                f"Cannot {action} Money with different currencies: "
                f"{self.currency.iso_code} and {other.currency.iso_code}"
            )

    # Convenience methods for currency checking
    def same_currency(self, other: Money) -> bool:
        """Check if two Money objects have the same currency."""
        return self.currency == other.currency

    def currency_mismatch(self, other: Money) -> bool:
        """Check if two Money objects have different currencies."""
        return self.currency != other.currency

    # endregion

    # region Splitting and Allocation

    def split(self, n: int) -> list[Self]:
        """
        Split money into n equal parts.
        
        Distributes the remainder across parts to ensure the sum equals the original.
        For negative amounts, distribute the remainder to the last parts.
        
        Args:
            n: Number of parts to split into (must be positive)
            
        Returns:
            List of n Money objects that sum to original
            
        Example:
            ```python
            bill = Money.mint(100.00, USD)
            shares = bill.split(3)
            # [Money(3334, USD), Money(3333, USD), Money(3333, USD)]
            # Sum: $100.00
            
            #noinspection GrazieInspection
            negative = Money.mint(-10.00, USD)
            shares = negative.split(3)
            # [Money(-334, USD), Money(-333, USD), Money(-333, USD)]
            # Sum: -$10.00
            ```
        """
        if n <= 0:
            raise ValueError(f"Cannot split into {n} parts (must be positive)")

        base_cents = self.amount_cents // n
        remainder = self.amount_cents % n  # This is always non-negative

        parts = []
        for i in range(n):
            # For positive amounts: add +1 to the first ` remainder ` parts
            # For negative amounts: add +1 to the last ` remainder ` parts (makes them less negative)
            # Python's modulo gives a non-negative remainder even for negative dividends
            extra = 0
            if self.amount_cents >= 0:
                # Positive: give extra to first parts
                if i < remainder:
                    extra = 1
            else:
                # Negative: give extra to last parts (to make them less negative)
                if i >= n - remainder:
                    extra = 1

            parts.append(Money.from_cents(base_cents + extra, self.currency))

        return parts

    def allocate(self, ratios: list[int | float | Decimal]) -> list[Self]:
        """
        Allocate money according to ratios.
        
        Useful for splitting payments proportionally (e.g., taxes, commissions).
        Handles rounding to ensure the sum equals the original.
        
        Args:
            ratios: List of ratios (doesn't need to sum to 1 or 100)
            
        Returns:
            List of Money objects allocated by ratio
            
        Example:
            ```python
            revenue = Money.mint(1000.00, USD)
            # 10% platform, 90% seller
            [platform, seller] = revenue.allocate([10, 90])
            # platform: $100.00, seller: $900.00
            ```
        """
        if not ratios or sum(ratios) == 0:
            raise ValueError("Ratios must be non-empty and sum to non-zero")

        total_ratio = sum(Decimal(str(r)) for r in ratios)
        if not ratios or total_ratio == 0:
            raise ValueError("Ratios must be non-empty and sum to non-zero")

        results = []

        for ratio in ratios:
            allocated_cents = (
                    Decimal(self.amount_cents) * Decimal(str(ratio)) / total_ratio
            ).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            results.append(Money.from_cents(int(allocated_cents), self.currency))

        # Adjust first allocation for rounding differences
        total_allocated = sum(m.amount_cents for m in results)
        difference = self.amount_cents - total_allocated

        if difference != 0:
            results[0] = Money.from_cents(
                results[0].amount_cents + difference,
                self.currency
            )

        return results

    # endregion

    # region Formatting

    def __str__(self) -> str:
        """
        Format for display using currency symbol.
        
        Returns:
            Formatted string like '$29.99' or '¥1000'
        """
        precision = self.currency.sub_unit_precision
        if precision == 0:
            return f"{self.currency.symbol}{self.amount_cents // self.currency.sub_units_per_unit}"
        return f"{self.currency.symbol}{self.amount}"

    def __repr__(self) -> str:
        """
        Developer representation.
        
        Returns:
            String like 'Money(2999, USD)'
        """
        return f"Money({self.amount_cents}, {self.currency.iso_code})"

    def format(self, show_currency: bool = True, symbol: str | None = None) -> str:
        """
        Format money with custom options.
        
        Args:
            show_currency: Include currency code (default: True)
            symbol: Override currency symbol (default: use currency's symbol)
            
        Returns:
            Formatted string
            
        Example:
            ```python
            price = Money.mint(29.99, USD)
            price.format() # '$29.99 USD'
            price.format(show_currency=False) # '$29.99'
            price.format(symbol='US$') # 'US$29.99 USD'
            ```
        """
        sym = symbol if symbol is not None else self.currency.symbol
        precision = self.currency.sub_unit_precision
        amount_str = f"{sym}{self.amount:.{precision}f}"

        if show_currency:
            return f"{amount_str} {self.currency.iso_code}"
        return amount_str

    # endregion


# region Legacy Helper Functions

def dollars_part(m: Money) -> int:
    """Legacy function: Get dollars part of money."""
    return m.dollars_part


def cents_part(m: Money) -> int:
    """Legacy function: Get cents part of money."""
    return m.cents_part


# endregion

# region Conversion Helpers for Migration

def to_money(value: int | float | Decimal | Money, currency: Currency = USD) -> Money:
    """
    Convert numeric value to Money (idempotent for Money inputs).

    Useful for Excel/CSV imports where data comes as primitive types.

    Args:
        value: Amount to convert (or Money to pass through)
        currency: Currency for new Money objects

    Returns:
        Money instance

    Example:
```python
        # Excel data
        excel_prices = [29.99, 49.99, 19.99]
        money_prices = [to_money(p, USD) for p in excel_prices]

        # Idempotent - safe to use on already-converted data
        price = to_money(Money.mint(10, USD), USD) # Returns same Money
```
    """
    if isinstance(value, Money):
        return value
    return Money.mint(value, currency)


def to_money_like(value: int | float | Decimal | Money, reference: Money) -> Money:
    """
    Convert value to Money using a reference object's currency.

    Useful for adjustments where the currency should match a base amount.

    Args:
        value: Amount to convert (or Money to validate)
        reference: Money object whose currency should be used

    Returns:
        Money instance with reference's currency

    Raises:
        TypeError: If value is Money with different currency than reference

    Example:
```python
        base_price = Money.mint(100, USD)
        discount_pct = 0.10 # From Excel
        discount = to_money_like(discount_pct * 100, base_price)
        final = base_price - discount
```
    """
    if isinstance(value, Money):
        if value.currency != reference.currency:
            raise TypeError(
                f"Currency mismatch: value is {value.currency.iso_code}, "
                f"reference is {reference.currency.iso_code}"
            )
        return value
    return Money.mint(value, reference.currency)

# endregion
