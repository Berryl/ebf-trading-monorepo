import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

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
    def fu(self, project_root: Path):
        from ebfutil.fileutil.file_util import FileUtil
        return FileUtil(project_root_override=project_root)

    @pytest.fixture
    def user_home(self, tmp_path: Path) -> Path:
        return tmp_path / "home"


class TestCreation(ConfigServiceFixture):
    def test_can_create_service(self, sut: ConfigService):
        assert isinstance(sut, ConfigService)

    def test_default_includes_yaml_loader(self, sut: ConfigService):
        # KISS: introspect by type name; no reliance on privates besides _loaders
        assert any(type(ldr) is YamlLoader for ldr in sut._loaders)


class TestLoad:
    def test_loads_project_yaml_only(self, sut: ConfigService, fu, project_root: Path):
        (project_root / "config").mkdir(parents=True)
        (project_root / "config" / "config.yaml").write_text(textwrap.dedent("""
            a: 1
            list: [1]
            nest: { x: 1, y: 1 }
        """).strip() + "\n")

        cfg, sources = sut.load(
            app_name="myapp",
            file_util=fu,
            search_path="config",
            filename="config.yaml",
            return_sources=True,
        )

        assert cfg == {"a": 1, "list": [1], "nest": {"x": 1, "y": 1}}
        assert sources == [project_root / "config" / "config.yaml"]

    def test_user_overrides_project_with_deep_merge_and_sources_order(
        self, sut: ConfigService, fu, project_root: Path, user_home: Path
    ):
        (project_root / "config").mkdir(parents=True)
        (user_home / ".config" / "myapp").mkdir(parents=True)

        # project base
        (project_root / "config" / "config.yaml").write_text(textwrap.dedent("""
            a: 1
            list: [1]
            nest:
              x: 1
              y: 1
            base: 1  # comment to ensure parser tolerates inline comments
        """).strip() + "\n")

        # user override (dict merge, list replace, scalar add/override)
        (user_home / ".config" / "myapp" / "config.yaml").write_text(textwrap.dedent("""
            b: 2
            list: [2]
            nest:
              y: 9
            base: 1  # still parses with comment
        """).strip() + "\n")

        with patch("ebfutil.fileutil.file_util.FileUtil.get_user_base_dir", return_value=user_home):
            cfg, sources = sut.load(
                app_name="myapp",
                file_util=fu,
                search_path="config",
                filename="config.yaml",
                return_sources=True,
            )

        assert cfg == {
            "a": 1,
            "b": 2,
            "list": [2],                 # list replaced
            "nest": {"x": 1, "y": 9},    # dict deep-merged
            "base": 1,
        }
        assert sources == [
            project_root / "config" / "config.yaml",
            user_home / ".config" / "myapp" / "config.yaml",
        ]
