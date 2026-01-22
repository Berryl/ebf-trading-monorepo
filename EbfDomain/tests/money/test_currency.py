import re

import pytest
from ebf_core.guards.guards import ContractError

from ebf_domain.money.currency import (
    Currency, USD, EUR, GBP, JPY,
    get_currency, register_currency, list_currencies
)


class TestCurrency:
    """Tests for Currency dataclass."""

    class TestIsoCode:

        @pytest.mark.parametrize('iso_code', ["usd", "jpy"])
        def test_iso_code_normalized_to_uppercase(self, iso_code):
            c = Currency(iso_code, '$', 'dollar', 'cent')

            assert c.iso_code == iso_code.upper()

        @pytest.mark.parametrize('iso_code', ["    "])
        def test_iso_code_must_be_valued(self, iso_code):
            with pytest.raises(ContractError, match="Arg 'iso_code' cannot be an empty string"):
                Currency(iso_code, '$', 'dollar', 'cent')

        @pytest.mark.parametrize('iso_code', ['US-DOLLAR', 'US'])
        def test_iso_code_length(self, iso_code):
            with pytest.raises(ContractError, match="Arg 'iso_code' must have an exact length of 3"):
                Currency(iso_code, '$', 'dollar', 'cent')

    class TestSymbol:

        def test_symbol_must_be_valued(self):
            with pytest.raises(ContractError):
                Currency("CCC", '    ', 'dollar', 'cent')

        def test_symbol_must_be_reasonable_length(self):
            with pytest.raises(ContractError):
                Currency("CCC", '123456', 'dollar', 'cent')

    class TestSubunits:

        def test_default_per_unit_is_100(self):
            cur = Currency('USD', '$', 'dollar', 'cent')

            assert cur.sub_units_per_unit == 100

        def test_default_precision_is_2(self):
            cur = Currency('USD', '$', 'dollar', 'cent')

            assert cur.sub_unit_precision == 2

        def test_with_per_unit_override(self):
            jpy = Currency('JPY', '¥', 'yen', 'sen', sub_units_per_unit=99)

            assert jpy.sub_units_per_unit == 99

        def test_with_precision_override(self):
            jpy = Currency('JPY', '¥', 'yen', 'sen', sub_unit_precision=99)

            assert jpy.sub_unit_precision == 99

        def test_display_name(self):
            assert USD.sub_unit_display_name == "cent (1/100 dollar)"
            assert JPY.sub_unit_display_name == "sen (1/1 yen)"

        def test_subunit_name_cannot_be_empty_str(self):
            with pytest.raises(ContractError):
                Currency('USD', '$', 'dollar', ' ')

        def test_subunit_cannot_be_negative(self):
            msg = "Arg 'sub_units_per_unit' must be positive"

            with pytest.raises(ContractError, match=msg):
                Currency('USD', '$', 'dollar', 'cent', sub_units_per_unit=-1)

        def test_subunit_cannot_be_zero(self):
            with pytest.raises(ContractError):
                Currency('USD', '$', 'dollar', 'cent', sub_units_per_unit=0)

        def test_precision_be_negative(self):
            msg = re.escape("Arg 'sub_unit_precision' must be non-negative (>= 0)")

            with pytest.raises(ContractError, match=msg):
                Currency('USD', '$', 'dollar', 'cent', sub_unit_precision=-1)

        def test_subunit_can_be_huge_value(self):
            huge = 10 ** 18
            btc = Currency('BTC', '₿', 'bitcoin', 'satoshi', sub_units_per_unit=huge)

            assert btc.sub_units_per_unit == huge

        def test_precision_can_be_huge_value(self):
            huge = 10 ** 18
            btc = Currency('BTC', '₿', 'bitcoin', 'satoshi', sub_unit_precision=huge)

            assert btc.sub_unit_precision == huge

    class TestImmutability:
        """Currency is immutable (frozen)."""

        def test_cannot_modify_iso_code(self):
            cur = USD
            with pytest.raises(Exception):  # FrozenInstanceError
                cur.iso_code = 'EUR'

        def test_cannot_modify_symbol(self):
            """Cannot modify a symbol after creation."""
            cur = USD
            with pytest.raises(Exception):
                cur.symbol = '€'

    class TestStringOverrides:

        def test_str_override(self):
            """str() returns 'CODE (SYMBOL)'."""
            assert str(USD) == "USD ($)"
            assert str(EUR) == "EUR (€)"

        def test_repr_override(self):
            """repr() returns constructor form."""
            assert repr(USD) == "Currency('USD', '$', 'dollar', 'cent')"

        def test_display_name(self):
            assert USD.display_name == "Dollar (USD)"
            assert EUR.display_name == "Euro (EUR)"

    class TestEquality:
        """Tests for currency equality and comparison."""

        def test_equality(self):
            c1 = get_currency('USD')
            c2 = get_currency('USD')

            assert c1 == c2

            eur = get_currency('EUR')
            assert c1 != eur

        def test_currencies_are_hashable(self):
            """Currencies can be used in sets/dicts."""
            currencies = {USD, EUR, GBP}

            assert len(currencies) == 3
            assert USD in currencies

        def test_can_use_as_dict_key(self):
            """Currencies can be dict keys."""
            exchange_rates = {
                USD: 1.0,
                EUR: 1.08,
                GBP: 1.26
            }

            assert exchange_rates[USD] == 1.0

    class TestConvenienceConstants:
        """Tests for predefined currency constants."""

        def test_usd_constant(self):
            """USD constant is properly configured."""
            assert USD.iso_code == 'USD'
            assert USD.symbol == '$'
            assert USD.sub_units_per_unit == 100

        def test_eur_constant(self):
            """EUR constant is properly configured."""
            assert EUR.iso_code == 'EUR'
            assert EUR.symbol == '€'
            assert EUR.sub_units_per_unit == 100

        def test_gbp_constant(self):
            """GBP constant is properly configured."""
            assert GBP.iso_code == 'GBP'
            assert GBP.symbol == '£'
            assert GBP.sub_unit_name == 'penny'

        def test_jpy_constant(self):
            """JPY has no sub-units (1:1 ratio)."""
            assert JPY.iso_code == 'JPY'
            assert JPY.sub_units_per_unit == 1
            assert JPY.sub_unit_precision == 0


class TestCurrencyRegistry:
    """Tests for currency registry functions."""

    class TestGetCurrency:

        def test_instances_are_same(self):
            assert get_currency('USD') is get_currency('USD')

        @pytest.mark.parametrize('iso_code', ['usd', 'UsD', 'USD'])
        def test_get_currency_by_code_is_case_insensitive(self, iso_code):
            assert get_currency(iso_code) == USD

        def test_get_currency_not_found(self):
            with pytest.raises(KeyError, match="Currency 'XXX' not found"):
                get_currency('XXX')

    def test_can_register_custom_currency(self):
        """Can register a custom currency."""
        custom = Currency('ZZZ', 'Z', 'zed', 'zoos')
        register_currency(custom)

        assert get_currency('ZZZ') == custom

    def test_list_currencies(self):
        """list_currencies returns all registered currencies."""
        currencies = list_currencies()

        assert len(currencies) > 0
        assert any(c.iso_code == 'USD' for c in currencies)
        assert any(c.iso_code == 'EUR' for c in currencies)

        # Should be sorted by ISO code
        iso_codes = [c.iso_code for c in currencies]
        assert iso_codes == sorted(iso_codes)
