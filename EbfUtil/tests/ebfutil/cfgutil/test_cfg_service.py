from pathlib import Path
from unittest.mock import MagicMock

import pytest
import yaml

from ebfutil.cfgutil import ConfigService
from ebfutil.cfgutil.loaders import YamlLoader
from ebfutil.fileutil.file_util import FileUtil


class ConfigServiceFixture:
    @pytest.fixture
    def sut(self) -> ConfigService:
        return ConfigService()

    @pytest.fixture
    def project_root(self, tmp_path: Path) -> Path:
        return tmp_path / "project"

    @pytest.fixture
    def user_home(self, tmp_path: Path) -> Path:
        return tmp_path / "home"

    @pytest.fixture
    def project_file_util(self, project_root: Path):
        from ebfutil.fileutil.file_util import FileUtil
        return FileUtil(project_root_override=project_root)

    @pytest.fixture
    def data(self) -> dict:
        return {"a": 1, "list": [1], "nest": {"x": 1, "y": 1}}

    @pytest.fixture
    def fake_project_file(self, project_root: Path, data: dict) -> Path:
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
    def test_can_load_project_config(self, sut: ConfigService, project_file_util, fake_project_file: Path, data: dict):
        cfg, sources = sut.load(app_name="myapp", return_sources=True, file_util=project_file_util)

        assert cfg == data
        assert sources == [fake_project_file]
        assert sources[0].name == "config.yaml"  # redundant but clear what the actual file source is

    def test_can_load_user_config_when_project_config_absent(self, sut: ConfigService, user_home: Path):
        u = user_home / ".config" / "myapp" / "config.yaml"
        u.parent.mkdir(parents=True, exist_ok=True)
        u.write_text(yaml.safe_dump({"a": 9, "list": [2], "nest": {"x": 5}}), encoding="utf-8")

        mock_fu = MagicMock(spec=FileUtil)
        mock_fu.try_get_file_from_project_root.return_value = None
        mock_fu.try_get_file_from_user_base_dir.return_value = u

        cfg, sources = sut.load(app_name="myapp", return_sources=True, file_util=mock_fu)

        assert cfg == {"a": 9, "list": [2], "nest": {"x": 5}}
        assert sources == [u]

    def test_user_cfg_has_precedence_over_project_cfg(self, sut: ConfigService, fake_project_file: Path,
                                                      user_home: Path):
        # user overrides: list replaced, dict deep-merged
        u = user_home / ".config" / "myapp" / "config.yaml"
        u.parent.mkdir(parents=True, exist_ok=True)
        u.write_text(yaml.safe_dump({"b": 2, "list": [2], "nest": {"y": 9}}), encoding="utf-8")

        mock_fu = MagicMock(spec=FileUtil)
        mock_fu.try_get_file_from_project_root.return_value = fake_project_file
        mock_fu.try_get_file_from_user_base_dir.return_value = u

        cfg, sources = sut.load(app_name="myapp", return_sources=True, file_util=mock_fu)

        assert cfg == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}
        assert sources == [fake_project_file, u]

    def test_when_no_files_found_at_all(self, sut: ConfigService):
        mock_fu = MagicMock(spec=FileUtil)
        mock_fu.try_get_file_from_project_root.return_value = None
        mock_fu.try_get_file_from_user_base_dir.return_value = None

        cfg, sources = sut.load(app_name="myapp", return_sources=True, file_util=mock_fu)

        assert cfg == {}
        assert sources == []

    def test_unknown_suffix_yields_empty_dict(self, sut: ConfigService, project_file_util, project_root: Path):
        p = project_root / "config" / "config.unknown"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("key=value\n", encoding="utf-8")

        cfg, sources = sut.load(app_name="myapp", filename="config.unknown",
                                return_sources=True, file_util=project_file_util)
        assert cfg == {}
        assert sources == [p]


class TestYamlSpecific(ConfigServiceFixture):
    def test_comments_are_ignored(self, sut: ConfigService, project_file_util, project_root: Path):
        p = project_root / "config" / "with_comments.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# top comment\nbase: 1\nnest:\n  k: v  # inline\n",
            encoding="utf-8",
        )
        cfg = sut.load(app_name="myapp", filename="with_comments.yaml", file_util=project_file_util)
        assert cfg == {"base": 1, "nest": {"k": "v"}}


class TestPublicApi(ConfigServiceFixture):

    def test_load_config(self, project_file_util, fake_project_file: Path, data: dict):
        from ebfutil.cfgutil import load_config
        cfg, sources = load_config(app_name="myapp", file_util=project_file_util, return_sources=True,)
        assert cfg == data
        assert sources == [fake_project_file]
