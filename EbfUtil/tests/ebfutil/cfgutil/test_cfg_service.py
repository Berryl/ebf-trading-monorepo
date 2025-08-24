import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from ebfutil.cfgutil import ConfigService
from ebfutil.cfgutil.loaders import YamlLoader


class ConfigServiceFixture:
    @pytest.fixture
    def sut(self) -> ConfigService:
        return ConfigService()

    @pytest.fixture
    def fu(self, project_root: Path):
        from ebfutil.fileutil.file_util import FileUtil
        return FileUtil(project_root_override=project_root)

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        return tmp_path / "project"

    @pytest.fixture
    def user_home(self, tmp_path: Path) -> Path:
        return tmp_path / "home"

    @pytest.fixture
    def data(self) -> dict:
        return {"a": 1, "list": [1], "nest": {"x": 1, "y": 1}}

    @pytest.fixture
    def fake_file(self, project_root: Path, data: dict) -> Path:
        tgt = project_root / "config" / "config.yaml"
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text(yaml.safe_dump(data), encoding="utf-8")
        return tgt


class TestCreation(ConfigServiceFixture):
    def test_can_create_service(self, sut: ConfigService):
        assert isinstance(sut, ConfigService)

    def test_default_includes_yaml_loader(self, sut: ConfigService):
        assert any(type(ldr) is YamlLoader for ldr in sut._loaders)


class TestLoad(ConfigServiceFixture):
    class TestLoad(ConfigServiceFixture):
        def test_can_load_yaml_files(self, sut: ConfigService, data, fu, fake_file):
            cfg, sources = sut.load(
                app_name="myapp",
                file_util=fu,
                search_path="config",
                project_filename="config.yaml",
                return_sources=True,
            )
            assert cfg == data
            assert sources == [fake_file]

