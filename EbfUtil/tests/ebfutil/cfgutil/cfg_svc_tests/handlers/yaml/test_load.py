import json
from pathlib import Path

import pytest

from ebfutil.cfgutil import ConfigService
from ebfutil.fileutil import FileUtil
from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class YamlConfigServiceFixture(ConfigServiceFixture):
    @pytest.fixture(scope="class")
    def default_ext(self) -> str:
        return ".yaml"

    @pytest.fixture(scope="class")
    def yaml_cfg_file(self, make_filename) -> str:
        return make_filename()

    @pytest.fixture
    def project_file(self, yaml_cfg_file: str, project_root: Path, project_search_path: str, data: dict) -> Path:
        tgt = project_root / project_search_path / yaml_cfg_file
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text(json.dumps(data), encoding="utf-8")
        return tgt

    @staticmethod
    def test_fixture_overrides(yaml_cfg_file):
        assert yaml_cfg_file == "config.yaml"


class TestLoad(YamlConfigServiceFixture):

    def test_can_load_project_config(self, sut: ConfigService, app_name, yaml_cfg_file,
                                     project_file_util, project_file: Path, data: dict
                                     ):
        cfg, sources = sut.load(app_name, filename=yaml_cfg_file, return_sources=True, file_util=project_file_util)

        assert cfg == data
        assert sources == [project_file]
        assert sources[0].name == yaml_cfg_file

    def test_can_load_user_config_when_project_config_absent(
            self, sut: ConfigService, mock_file_util: FileUtil, user_config_factory, app_name: str):

        user_data = {"a": 9, "list": [2], "nest": {"x": 5}}
        user_cfg: Path = user_config_factory(user_data)

        mock_file_util.try_get_file_from_project_root.return_value = None
        mock_file_util.try_get_file_from_user_base_dir.return_value = user_cfg

        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)

        assert cfg == user_data
        assert sources == [user_cfg]
