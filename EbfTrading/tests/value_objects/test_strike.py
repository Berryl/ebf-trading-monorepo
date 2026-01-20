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
