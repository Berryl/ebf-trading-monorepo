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
