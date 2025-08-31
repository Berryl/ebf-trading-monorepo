import json
from pathlib import Path

import pytest

from ebfutil.cfgutil import ConfigService
from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class JsonConfigServiceFixture(ConfigServiceFixture):
    @pytest.fixture(scope="class")
    def default_ext(self) -> str:
        return ".json"

    @pytest.fixture(scope="class")
    def json_cfg_file(self, make_filename) -> str:
        return make_filename()

    @pytest.fixture
    def project_file(self, json_cfg_file: str, project_root: Path, project_search_path: str, data: dict) -> Path:
        tgt = project_root / project_search_path / json_cfg_file
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text(json.dumps(data), encoding="utf-8")
        return tgt

    @staticmethod
    def test_fixture_overrides(json_cfg_file):
        assert json_cfg_file == "config.json"


class TestLoad(JsonConfigServiceFixture):

    def test_can_load_project_config(
            self, sut: ConfigService, app_name, json_cfg_file,project_file_util, project_file: Path, data: dict
    ):
        cfg, sources = sut.load(app_name, filename=json_cfg_file, return_sources=True, file_util=project_file_util)

        assert cfg == data
        assert sources == [project_file]
        assert sources[0].name == json_cfg_file
