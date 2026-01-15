from dataclasses import dataclass

import ebf_core.guards.guards as g


@dataclass(frozen=True)
class Currency:
    """
    Represents a form of money issued by a central authority.
    
    Encapsulates ISO currency code, symbol, name, and sub-unit information.
    Currencies are immutable value objects that can be safely reused.
    
    Attributes:
        iso_code: Three-letter ISO 4217 currency code (e.g., 'USD', 'EUR')
        symbol: Currency symbol for display (e.g., '$', '€')
        name: Full name of the major unit (e.g., 'dollar', 'euro')
        sub_unit_name: Name of the minor unit (e.g., 'cent', 'penny')
        sub_units_per_unit: Number of sub-units per major unit (default: 100)
        sub_unit_precision: Decimal places for display (default: 2)
    
    Usage:
        ```python
        # Create currency
        usd = Currency('USD', '$', 'dollar', 'cent')
        
        # Most currencies use 100 sub-units
        eur = Currency('EUR', '€', 'euro', 'cent')
        
        # Some use different ratios
        jpy = Currency('JPY', '¥', 'yen', 'sen', sub_units_per_unit=1, sub_unit_precision=0)
        ```
    
    Note:
        Based on py-moneyed: https://github.com/py-moneyed/py-moneyed
    """
    iso_code: str
    symbol: str
    name: str
    sub_unit_name: str
    sub_units_per_unit: int = 100
    sub_unit_precision: int = 2

    def __post_init__(self):
        g.ensure_str_is_valued(self.iso_code, 'iso_code')
        g.ensure_str_exact_length(self.iso_code, 3, 'iso_code')
        object.__setattr__(self, 'iso_code', self.iso_code.upper())

        g.ensure_str_is_valued(self.symbol, "symbol")
        g.ensure_str_max_length(self.symbol, 5, 'symbol')

        g.ensure_str_is_valued(self.name, "name")
        g.ensure_str_is_valued(self.sub_unit_name, "sub_unit_name")

        g.ensure_positive_number(self.sub_units_per_unit, description="sub_units_per_unit", allow_zero=False)
        g.ensure_positive_number(self.sub_unit_precision, description="sub_unit_precision", allow_zero=True)

    def __str__(self) -> str:
        """String representation: 'USD ($)'"""
        return f"{self.iso_code} ({self.symbol})"

    def __repr__(self) -> str:
        """Developer representation."""
        return (f"Currency('{self.iso_code}', '{self.symbol}', "
                f"'{self.name}', '{self.sub_unit_name}')")

    @property
    def display_name(self) -> str:
        """Full display name: 'United States Dollar (USD)'"""
        return f"{self.name.title()} ({self.iso_code})"

    @property
    def sub_unit_display_name(self) -> str:
        """Sub-unit display: 'cent (1/100 dollar)'"""
        return f"{self.sub_unit_name} (1/{self.sub_units_per_unit} {self.name})"


# region Common Currency Instances

# Major World Currencies
USD = Currency('USD', '$', 'dollar', 'cent')
EUR = Currency('EUR', '€', 'euro', 'cent')
GBP = Currency('GBP', '£', 'pound', 'penny')
JPY = Currency('JPY', '¥', 'yen', 'sen', sub_units_per_unit=1, sub_unit_precision=0)
CHF = Currency('CHF', 'Fr', 'franc', 'rappen')
CNY = Currency('CNY', '¥', 'yuan', 'fen')
CAD = Currency('CAD', 'C$', 'dollar', 'cent')
AUD = Currency('AUD', 'A$', 'dollar', 'cent')

# Other Major Currencies
INR = Currency('INR', '₹', 'rupee', 'paisa')
BRL = Currency('BRL', 'R$', 'real', 'centavo')
MXN = Currency('MXN', 'Mex$', 'peso', 'centavo')
RUB = Currency('RUB', '₽', 'ruble', 'kopek')

# Cryptocurrencies (for demonstration)
BTC = Currency('BTC', '₿', 'bitcoin', 'satoshi', sub_units_per_unit=100_000_000, sub_unit_precision=8)
ETH = Currency('ETH', 'Ξ', 'ether', 'wei', sub_units_per_unit=10 ** 18, sub_unit_precision=18)

# endregion


# region Currency Registry

# All registered currencies
_CURRENCY_REGISTRY: dict[str, Currency] = {
    'USD': USD,
    'EUR': EUR,
    'GBP': GBP,
    'JPY': JPY,
    'CHF': CHF,
    'CNY': CNY,
    'CAD': CAD,
    'AUD': AUD,
    'INR': INR,
    'BRL': BRL,
    'MXN': MXN,
    'RUB': RUB,
    'BTC': BTC,
    'ETH': ETH,
}


def get_currency(iso_code: str) -> Currency:
    """
    Get a currency by ISO code.
    
    Args:
        iso_code: Three-letter ISO 4217 code (case-insensitive)
        
    Returns:
        Currency instance
        
    Raises:
        KeyError: If the currency is not found
        
    Example:
        ```python
        usd = get_currency('USD')
        eur = get_currency('eur') # Case-insensitive
        ```
    """
    code = iso_code.upper()
    if code not in _CURRENCY_REGISTRY:
        raise KeyError(f"Currency '{iso_code}' not found in registry.")
    return _CURRENCY_REGISTRY[code]


def register_currency(currency: Currency) -> None:
    """
    Register a custom currency.
    
    Args:
        currency: Currency to register
        
    Example:
        ```python
        # Register a custom currency
        custom = Currency('XXX', 'X', 'custom', 'unit')
        register_currency(custom)
        ```
    """
    if currency.iso_code not in _CURRENCY_REGISTRY:
        _CURRENCY_REGISTRY[currency.iso_code] = currency


def list_currencies() -> list[Currency]:
    """
    Get all registered currencies.
    
    Returns:
        List of Currency instances sorted by ISO code
    """
    return sorted(_CURRENCY_REGISTRY.values(), key=lambda c: c.iso_code)

# endregion
