import pytest
from ebf_core.guards.guards import ContractError
from ebf_domain.money.currency import USD
from ebf_domain.money.money import Money

from ebf_trading.domain.value_objects.options.strike import Strike


class TestStrike:

    def test_init(self):
        m = Money(50, USD)
        assert Strike(m).price == m

    def test_must_be_positive(self):
        with pytest.raises(ContractError, match="Strike price"):
            Strike(Money.mint(-10, USD))

    def test_from_amount(self):
        strike = Strike.from_amount(100.50)
        assert strike.price == Money.mint(100.50, USD)

    def test_to_occ_format(self):
        strike = Strike.from_amount(42.50)
        assert strike.to_occ_format() == "00042500"

    def test_from_occ_format(self):
        strike = Strike.from_occ_format("00042500")
        assert strike.price == Money.mint(42.50, USD)

    @pytest.mark.parametrize("value", ["", "123", "123456789"])
    def test_occ_str_must_be_8_chars(self, value: str):
        with pytest.raises(ContractError, match="OCC symbol"):
            Strike.from_occ_format(value)

    @pytest.mark.parametrize("value", ["0004x500"])
    def test_occ_str_must_be_digits(self, value: str):
        with pytest.raises(ValueError, match=value):
            Strike.from_occ_format(value)
