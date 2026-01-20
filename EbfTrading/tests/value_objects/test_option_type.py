import pytest
from ebf_core.guards.guards import ContractError

from ebf_trading.domain.value_objects.options.option_type import OptionType


class TestOptionType:

    def test_is_call(self):
        assert OptionType.CALL.is_call
        assert not OptionType.PUT.is_call

    def test_is_put(self):
        assert not OptionType.CALL.is_put
        assert OptionType.PUT.is_put

    def test_str(self):
        assert str(OptionType.CALL) == "call"
        assert str(OptionType.PUT) == "put"

    def test_to_occ_format(self):
        assert OptionType.CALL.to_occ_format() == "C"
        assert OptionType.PUT.to_occ_format() == "P"

    def test_from_occ_format(self):
        assert OptionType.from_occ_format('c') == OptionType.CALL

    @pytest.mark.parametrize("value", ["", "123", "123456789"])
    def test_occ_str_must_be_1_char(self, value: str):
        with pytest.raises(ContractError, match="OCC symbol"):
            OptionType.from_occ_format(value)

    @pytest.mark.parametrize("value", ["x", "5"])
    def test_occ_str_must_be_c_or_p(self, value: str):
        with pytest.raises(ValueError, match="must be C or P"):
            OptionType.from_occ_format(value)
