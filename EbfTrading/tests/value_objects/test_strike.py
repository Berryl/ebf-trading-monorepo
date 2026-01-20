from ebf_domain.money.currency import USD
from ebf_domain.money.money import Money

from ebf_trading.domain.value_objects.options.strike import Strike


class TestStrike:
    def test_init(self):
        m = Money(50, USD)
        assert Strike(m).price == m

    def test_from_amount(self):
        strike = Strike.from_amount(100.50)
        assert strike.price == Money.mint(100.50, USD)
