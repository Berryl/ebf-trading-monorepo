from pathlib import Path

from ebfutil.cfgutil import ConfigService
from ebfutil.fileutil import FileUtil
from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class TestLoad(ConfigServiceFixture):
    def test_can_load_project_config(self, sut: ConfigService, project_file_util, fake_project_file: Path, data: dict):
        cfg, sources = sut.load(app_name="myapp", return_sources=True, file_util=project_file_util)

        assert cfg == data
        assert sources == [fake_project_file]
        assert sources[0].name == "config.yaml"  # redundant but clear what the actual file source is

    def test_can_load_user_config_when_project_config_absent(
            self, sut: ConfigService, mock_file_util: FileUtil, user_config_factory, app_name: str):
        u = user_config_factory({"a": 9, "list": [2], "nest": {"x": 5}})

        mock_file_util.try_get_file_from_project_root.return_value = None
        mock_file_util.try_get_file_from_user_base_dir.return_value = u

        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)

        assert cfg == {"a": 9, "list": [2], "nest": {"x": 5}}
        assert sources == [u]

    def test_user_cfg_has_precedence_over_project_cfg(
            self, sut: ConfigService,
            user_config_factory, mock_file_util: FileUtil,
            fake_project_file: Path, app_name: str):
        # user overrides: list replaced, dict deep-merged
        u = user_config_factory({"b": 2, "list": [2], "nest": {"y": 9}})

        mock_file_util.try_get_file_from_project_root.return_value = fake_project_file
        mock_file_util.try_get_file_from_user_base_dir.return_value = u

        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)

        assert cfg == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}
        assert sources == [fake_project_file, u]

    def test_when_no_files_found_at_all(self, sut: ConfigService, mock_file_util: FileUtil, app_name: str):
        mock_file_util.try_get_file_from_project_root.return_value = None
        mock_file_util.try_get_file_from_user_base_dir.return_value = None

        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)

        assert cfg == {}
        assert sources == []

    def test_unknown_suffix_yields_empty_dict(
            self, sut: ConfigService, project_file_util, project_root: Path, app_name: str):
        p = project_root / "config" / "config.unknown"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("key=value\n", encoding="utf-8")

        cfg, sources = sut.load(app_name=app_name, filename="config.unknown",
                                return_sources=True, file_util=project_file_util)
        assert cfg == {}
        assert sources == [p]
