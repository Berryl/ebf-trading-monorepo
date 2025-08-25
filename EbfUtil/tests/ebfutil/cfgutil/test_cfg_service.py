from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

from ebfutil.cfgutil import ConfigService
from ebfutil.cfgutil.loaders import YamlLoader


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
        cfg, sources = sut.load(
            app_name="myapp",
            file_util=project_file_util,
            project_search_path="config",
            return_sources=True,
        )
        assert cfg == data
        assert sources == [fake_project_file]
        assert sources[0].name == "config.yaml"

    def test_can_load_user_config_when_no_project_config(self, sut: ConfigService, user_home: Path):
        u = user_home / ".config" / "myapp" / "config.yaml"
        u.parent.mkdir(parents=True, exist_ok=True)
        u.write_text(yaml.safe_dump({"a": 9, "list": [2], "nest": {"x": 5}}), encoding="utf-8")

        mock_fu = MagicMock()
        mock_fu.try_get_file_from_project_root.return_value = None
        mock_fu.try_get_file_from_user_base_dir.return_value = u
        mock_fu.get_user_base_dir.return_value = user_home

        cfg, sources = sut.load(app_name="myapp", file_util=mock_fu, return_sources=True,)

        assert cfg == {"a": 9, "list": [2], "nest": {"x": 5}}
        assert sources == [u]

    def test_both_precedence_and_merge(self, sut: ConfigService, project_file_util, fake_project_file: Path, user_home: Path):
        # project has base; user overrides: list replace, dict deep-merge
        u = user_home / ".config" / "myapp" / "config.yaml"
        u.parent.mkdir(parents=True, exist_ok=True)
        u.write_text(yaml.safe_dump({"b": 2, "list": [2], "nest": {"y": 9}}), encoding="utf-8")

        with patch.object(project_file_util, "get_user_base_dir", return_value=user_home):
            cfg, sources = sut.load(
                app_name="myapp",
                file_util=project_file_util,
                project_search_path="config",
                project_filename="config.yaml",
                user_filename="config.yaml",
                return_sources=True,
            )

        assert cfg == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}
        assert sources == [fake_project_file, u]

    def test_no_files_found(self, sut: ConfigService, project_file_util):
        cfg, sources = sut.load(
            app_name="myapp",
            file_util=project_file_util,
            project_filename="missing.yaml",
            user_filename="missing.yaml",
            return_sources=True,
        )
        assert cfg == {}
        assert sources == []

    def test_project_only_no_sources(self, sut: ConfigService, project_file_util, fake_project_file: Path, data: dict):
        cfg = sut.load(
            app_name="myapp",
            file_util=project_file_util,
            project_search_path="config",
            return_sources=False,
        )
        assert cfg == data

    def test_yaml_with_comments(self, sut: ConfigService, project_file_util, project_root: Path):
        p = project_root / "config" / "with_comments.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# top comment\nbase: 1\nnest:\n  k: v  # inline\n",
            encoding="utf-8",
        )
        cfg = sut.load(
            app_name="myapp",
            file_util=project_file_util,
            project_search_path="config",
            project_filename="with_comments.yaml",
        )
        assert cfg == {"base": 1, "nest": {"k": "v"}}

    def test_unknown_suffix_yields_empty_dict(self, sut: ConfigService, project_file_util, project_root: Path):
        p = project_root / "config" / "config.unknown"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("key=value\n", encoding="utf-8")

        cfg, sources = sut.load(
            app_name="myapp",
            file_util=project_file_util,
            project_search_path="config",
            project_filename="config.unknown",
            return_sources=True,
        )
        assert cfg == {}
        assert sources == [p]

    def test_public_api_load_config(self, project_file_util, fake_project_file: Path, data: dict):
        from ebfutil.cfgutil import load_config
        cfg, sources = load_config(
            app_name="myapp",
            project_filename="config.yaml",
            user_filename="config.yaml",
            file_util=project_file_util,
            search_path="config",
            return_sources=True,
        )
        assert cfg == data
        assert sources == [fake_project_file]
