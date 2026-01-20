"""
Option ticker format converter.

Converts between Option value objects and various ticker formats.
Supports OCC (Option Clearing Corporation) standard format.
"""

from datetime import date
from decimal import Decimal

from ebf_trading.domain.value_objects.options.option import Option
from ebf_trading.domain.value_objects.ticker import Ticker
from ebf_trading.domain.value_objects.options.strike import Strike
from ebf_trading.domain.value_objects.options.option_type import OptionType


class OptionSymbolConverter:
    """
    Convert between Option objects and ticker formats.

    Currently, supports:
    - OCC (Option Clearing Corporation) standard format

    Future formats can be added (Tradier, TOS, Interactive Brokers, Fidelity, etc.)

    Usage:
        ```python
        # Convert Option to OCC ticker
        option = Option(...)
        occ_symbol = OptionSymbolConverter.to_occ(option)
        # 'HOG   010928P00042500'

        # Parse OCC ticker to an Option.
        option = OptionSymbolConverter.from_occ('HOG010928P00042500')
        ```
    """

    @staticmethod
    def to_occ(option: Option) -> str:
        """
        Generate OCC (Option Clearing Corporation) standard option ticker.

        Format: [Ticker-6chars][YYMMDD][C/P][Strike-8digits]

        The strike is represented as 8 digits:
        - 5 digits before decimal point
        - 3 digits after decimal point

        Args:
            option: Option to convert

        Returns:
            OCC ticker string

        Example:
            ```python
            # HOG $42.50 Put expiring 9/28/2001
            option = Option(
                underlying=Ticker('HOG'),
                strike=Strike.from_amount(42.50),
                option_type=OptionType.PUT,
                expiration=date (2001, 9, 28)
            )

            ticker = OptionSymbolConverter.to_occ(option)
            assert ticker == 'HOG010928P00042500'
            ```
        """
        # Underlying (6 chars, right-padded with spaces)
        ticker = option.underlying.ticker.ljust(6)

        # Expiration (YYMMDD)
        exp_str = option.expiration.strftime('%y%m%d')

        # Type (C or P)
        type_char = 'C' if option.is_call else 'P'

        # Strike (8 digits: whole dollars + cents, e.g., 00042500 for $42.50)
        # Multiply by 1000 to get millidollars, then format as 8 digits
        strike_millidollars = int(option.strike.price.amount * 1000)
        strike_str = f"{strike_millidollars:08d}"

        return f"{ticker}{exp_str}{type_char}{strike_str}"

    @staticmethod
    def from_occ(occ_symbol: str) -> Option:
        """
        Parse an OCC standard option ticker into an Option object.

        Format: [Ticker-6chars][YYMMDD][C/P][Strike-8digits]

        Args:
            occ_symbol: OCC format string (e.g., 'HOG   010928P00042500')

        Returns:
            New Option instance

        Raises:
            ValueError: If the ticker format is invalid

        Example:
            ```python
            option = OptionSymbolConverter.from_occ('HOG   010928P00042500')

            assert option.underlying.ticker == 'HOG'
            assert option.strike.price.amount == Decimal('42.50')
            assert option.is_put
            assert option.expiration == date(2001, 9, 28)
            ```
        """
        # Validate length
        if len(occ_symbol) != 21:
            raise ValueError(
                f"OCC ticker must be exactly 21 characters (got {len(occ_symbol)})"
            )

        # Parse components
        ticker_str = occ_symbol[0:6].strip()  # Ticker (6 chars, right-padded)
        exp_str = occ_symbol[6:12]  # YYMMDD (6 chars)
        type_char = occ_symbol[12]  # C or P (1 char)
        strike_str = occ_symbol[13:21]  # Strike (8 digits)

        # Validate and convert ticker
        if not ticker_str:
            raise ValueError("Ticker portion of OCC ticker cannot be empty")
        ticker = Ticker(ticker_str)

        # Validate and convert expiration date
        try:
            year = int(exp_str[0:2]) + 2000  # YY -> YYYY
            month = int(exp_str[2:4])
            day = int(exp_str[4:6])
            expiration = date(year, month, day)
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid expiration date in OCC ticker: {exp_str}") from e

        # Validate and convert the option type
        if type_char not in ('C', 'P'):
            raise ValueError(f"Invalid option type in OCC ticker: {type_char} (must be C or P)")
        option_type = OptionType.CALL if type_char == 'C' else OptionType.PUT

        # Validate and convert strike price
        try:
            strike_millidollars = int(strike_str)
            strike_amount = Decimal(strike_millidollars) / 1000
            strike = Strike.from_amount(float(strike_amount))
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid strike price in OCC ticker: {strike_str}") from e

        return Option(
            underlying=ticker,
            strike=strike,
            option_type=option_type,
            expiration=expiration
        )