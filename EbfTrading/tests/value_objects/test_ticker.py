import pytest
from ebf_core.guards.guards import ContractError

from ebf_trading.domain.value_objects.ticker import Ticker


class TestTicker:
    def test_valid_ticker(self):
        ticker = Ticker("HOG")
        assert ticker.symbol == "HOG"

    @pytest.mark.parametrize("value", ["123455678901"])
    def test_ticker_cannot_exceed_10_chars(self, value: str):
        with pytest.raises(ContractError, match="Arg 'symbol' must have a maximum length of 10"):
            Ticker(value)