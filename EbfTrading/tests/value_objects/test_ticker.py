import pytest
from ebf_core.guards.guards import ContractError

from ebf_trading.domain.value_objects.ticker import Ticker


class TestTicker:
    def test_valid_ticker(self):
        ticker = Ticker("HOG")
        assert ticker.ticker == "HOG"

    @pytest.mark.parametrize("value", ["hog"])
    def test_ticker_is_upper__cased(self, value: str):
        assert Ticker(value).ticker == "HOG"

    @pytest.mark.parametrize("value", ["123455678901"])
    def test_ticker_cannot_exceed_10_chars(self, value: str):
        with pytest.raises(ContractError, match="Arg 'ticker' must have a maximum length of 10"):
            Ticker(value)

    @pytest.mark.parametrize("value", ["       "])
    def test_ticker_must_be_valued(self, value: str):
        with pytest.raises(ContractError, match="cannot be an empty string"):
            Ticker(value)


    @pytest.mark.parametrize("value", ["123456789"])
    def test_occ_str_must_be_max_6_chars(self, value: str):
        with pytest.raises(ContractError, match="OCC ticker"):
            Ticker.from_occ_format(value)

    @pytest.mark.parametrize(("raw", "expected"),[
                                 ("hog", "HOG   "),
        ("gold", "GOLD  "),
        ("fiver", "FIVER "),
        ("mighty", "MIGHTY"),
    ])
    def test_from_occ_str_returns_padded_value(self, raw: str, expected: str):
        result = Ticker.from_occ_format(raw)
        assert result.ticker == expected
        assert len(result.ticker) == 6
