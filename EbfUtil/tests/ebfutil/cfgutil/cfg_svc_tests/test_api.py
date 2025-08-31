from pathlib import Path

import yaml

from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class TestPublicApi(ConfigServiceFixture):

    def test_load_config(self, project_file_util, fake_project_file: Path, data: dict, app_name: str):
        from ebfutil.cfgutil import load_config
        cfg, sources = load_config(app_name=app_name, file_util=project_file_util, return_sources=True, )
        assert cfg == data
        assert sources == [fake_project_file]

    def test_store_config(self, app_name: str, user_home: Path, mock_file_util, data: dict):
        from ebfutil.cfgutil import store_config

        mock_file_util.get_user_base_dir.return_value = user_home

        out_path = store_config(
            cfg=data,
            app_name=app_name,
            user_filename="config.yaml",
            target="user",
            file_util=mock_file_util,
        )
        expected_path = user_home / ".config" / app_name / "config.yaml"
        self._assert_stored_output_path_is(out_path, expected_path)

        persisted = yaml.safe_load(out_path.read_text(encoding="utf-8")) or {}
        assert persisted == data
