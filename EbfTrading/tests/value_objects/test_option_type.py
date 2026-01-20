from ebf_trading.domain.value_objects.options.option_type import OptionType


class TestOptionType:

    def test_is_call(self):
        assert OptionType.CALL.is_call
        assert not OptionType.PUT.is_call

    def test_is_put(self):
        assert not OptionType.CALL.is_put
        assert OptionType.PUT.is_put