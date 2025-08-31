from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class TestStore(ConfigServiceFixture):
    def test_store_config_callable(self):
        from ebfutil.cfgutil import store_config
        assert callable(store_config)
