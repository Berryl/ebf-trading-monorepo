import pytest

from ebfutil.cfgutil import ConfigService
from ebfutil.cfgutil.loaders import YamlLoader


class ConfigServiceFixture:
    @pytest.fixture
    def sut(self) -> ConfigService:
        return ConfigService()


class TestCreation(ConfigServiceFixture):
    def test_can_create_service(self, sut: ConfigService):
        assert isinstance(sut, ConfigService)

    def test_default_includes_yaml_loader(self, sut: ConfigService):
        # KISS: introspect by type name; no reliance on privates besides _loaders
        assert any(type(l) is YamlLoader for l in sut._loaders)


class TestLoad:
    pass
