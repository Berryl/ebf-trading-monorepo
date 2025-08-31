from pathlib import Path
from typing import Protocol
from unittest.mock import MagicMock

import pytest
import yaml

from ebfutil.cfgutil import ConfigService
from ebfutil.fileutil.file_util import FileUtil


class ConfigServiceFixture:

    # region class-scoped
    @pytest.fixture(scope="class")
    def app_name(self) -> str:
        return "myapp"

    @pytest.fixture(scope="class")
    def project_search_path(self) -> str:
        return "config"

    @pytest.fixture(scope="class")
    def filename_base(self) -> str:
        """Base filename without extension."""
        return "config"

    @pytest.fixture(scope="class")
    def default_ext(self) -> str:
        """Default extension used when tests do not specify one."""
        return ".yaml"

    @pytest.fixture(scope="class")
    def data(self) -> dict:
        return {"a": 1, "list": [1], "nest": {"x": 1, "y": 1}}

    @pytest.fixture(scope="class")
    def make_filename(self, filename_base: str, default_ext: str):
        """Helper to build a filename with a given extension (defaults to default_ext)."""
        def _make(ext: str | None = None) -> str:
            e = ext or default_ext
            if not e.startswith("."):
                e = f".{e}"
            return f"{filename_base}{e}"
        return _make

    @pytest.fixture(scope="class")
    def filename(self, make_filename):
        """Keeps backward compatibility for tests expecting 'filename'."""
        return make_filename()

    # endregion

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
        return FileUtil(project_root_override=project_root)

    @pytest.fixture
    def fake_project_file(self, project_root: Path, data: dict) -> Path:
        tgt = project_root / "config" / "config.yaml"
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text(yaml.safe_dump(data), encoding="utf-8")
        return tgt

    @pytest.fixture
    def mock_file_util(self):
        return MagicMock(spec=FileUtil)

    # region User Config Factory
    class UserConfigWriter(Protocol):
        def __call__(
                self,
                payload: dict,
                *,
                file_name: str | None = None,
                app: str | None = None,
        ) -> Path: ...

    @pytest.fixture
    def user_config_factory(
            self,
            user_home: Path,
            app_name: str,
            make_filename
    ) -> UserConfigWriter:
        """
        Returns a callable to create a user config file under:
          <user_home>/.config/<app_name>/<filename or custom>

        Usage:
            path = user_config_factory({"k": "v"})
            path = user_config_factory({"k": "v"}, file_name="alt.yaml")
            path = user_config_factory({"k": "v"}, app="other-app")
        """

        def _create_user_cfg(
                payload: dict,
                *,
                file_name: str | None = None,
                app: str | None = None
        ) -> Path:
            tgt_app = app or app_name
            f = file_name or make_filename()

            p = user_home / ".config" / tgt_app / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(yaml.safe_dump(payload), encoding="utf-8")
            return p

        return _create_user_cfg
    # endregion
