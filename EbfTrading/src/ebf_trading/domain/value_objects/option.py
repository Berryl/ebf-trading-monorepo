"""
Option contract value object.
"""

from dataclasses import dataclass
from datetime import date, datetime

from ebf_core.guards import guards as g
from ebf_trading.domain.value_objects.ticker import Ticker
from ebf_trading.domain.value_objects.strike import Strike
from ebf_trading.domain.value_objects.option_type import OptionType


@dataclass(frozen=True)
class Option:
    """
    Represents an option contract specification.

    An option combines underlying ticker, strike price, option type (call/put),
    and expiration date to uniquely identify a tradeable option contract.

    This is a pure value object - format conversions (e.g., OCC symbols) are
    handled by OptionSymbolConverter.

    Attributes:
        underlying: The underlying security ticker
        strike: The strike price
        option_type: CALL or PUT
        expiration: Expiration date (market close on this date)

    Usage:
        ```python
        # Create an IBM $42.50 put expiring 9/28/2001
        option = Option(
            underlying=Ticker('IBM'),
            strike=Strike.from_amount(42.50),
            option_type=OptionType.PUT,
            expiration=date(2001, 9, 28)
        )

        # Check properties
        assert option.is_put
        assert option.underlying.symbol == 'IBM'

        # Display (human-readable)
        print(option) # "IBM $42.50 Put 2001-09-28"
        ```
    """
    underlying: Ticker
    strike: Strike
    option_type: OptionType
    expiration: date

    def __post_init__(self):
        g.ensure_not_none(self.underlying, "underlying")
        g.ensure_not_none(self.strike, "strike")
        g.ensure_not_none(self.option_type, "option_type")
        g.ensure_type(self.expiration, datetime, "expiration")

    @property
    def is_call(self) -> bool:
        """True if this is a CALL option."""
        return self.option_type.is_call

    @property
    def is_put(self) -> bool:
        """True if this is a PUT option."""
        return self.option_type.is_put

    @property
    def ticker_symbol(self) -> str:
        """Get the underlying ticker symbol as a string."""
        return self.underlying.symbol

    @property
    def strike_price(self):
        """Get the strike price Money object."""
        return self.strike.price

    def days_to_expiration(self, as_of: date | None = None) -> int:
        """
        Calculate days to expiration.

        Args:
            as_of: Reference date (default: today)

        Returns:
            Number of days until expiration (can be negative if expired)

        Example:
            ```python
            option = Option(...)
            dte = option.days_to_expiration(date(2001, 9, 11))
            # Returns 17 for 9/28/2001 expiration
            ```
        """
        reference = as_of if as_of else date.today()
        return (self.expiration - reference).days

    def is_expired(self, as_of: date | None = None) -> bool:
        """
        Check if the option has expired.

        Args:
            as_of: Reference date (default: today)

        Returns:
            True if the expiration date has passed
        """
        reference = as_of if as_of else date.today()
        return self.expiration < reference

    def __str__(self) -> str:
        """
        Human-readable option description.

        Format: 'IBM $42.50 Put 2001-09-28'

        Returns:
            Formatted display string
        """
        option_type_name = "Call" if self.is_call else "Put"
        return f"{self.underlying.symbol} {self.strike.price} {option_type_name} {self.expiration}"

    def __repr__(self) -> str:
        """Developer representation."""
        return (f"Option({self.underlying.symbol}, {self.strike.price.amount}, "
                f"{self.option_type}, {self.expiration})")