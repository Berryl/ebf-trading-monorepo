import yaml
from pathlib import Path
from unittest.mock import patch
import pytest

from ebfutil.fileutil.file_util import FileUtil
from ebfutil.cfgutil import load_config


def _dump_yaml(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


@pytest.fixture
def proj(tmp_path: Path) -> Path:
    return tmp_path / "proj"


@pytest.fixture
def file_util(proj: Path) -> FileUtil:
    return FileUtil(project_root_override=proj)


class TestProjectConfigLoad:
    def test_load_uses_project_root_when_present(self, proj: Path, file_util: FileUtil):
        cfg_file = proj / "config" / "config.yaml"
        _dump_yaml(cfg_file, {"a": 1, "b": {"c": 2}})

        cfg, used = load_config(
            app_name="dummy",
            file_util=file_util,
            search_path="config",
            filename="config.yaml",
            return_sources=True,
        )

        assert cfg == {"a": 1, "b": {"c": 2}}
        assert used and used[0] == cfg_file


class TestUserOverridePrecedence:
    @pytest.fixture
    def user_base(self, tmp_path: Path) -> Path:
        # simulate home/.config
        return tmp_path / "home" / ".config"

    def test_user_override_wins_over_project(
        self, proj: Path, file_util: FileUtil, user_base: Path
    ):
        proj_cfg = proj / "config" / "config.yaml"
        _dump_yaml(proj_cfg, {"theme": "light", "paths": {"data": "/proj"}})

        user_cfg = user_base / "myapp" / "config.yaml"
        _dump_yaml(user_cfg, {"theme": "dark", "paths": {"log": "/user/logs"}})

        with patch.object(FileUtil, "get_user_base_dir", return_value=user_base.parent):
            cfg, used = load_config(
                app_name="myapp",
                file_util=file_util,
                search_path="config",
                filename="config.yaml",
                return_sources=True,
            )

        assert cfg["theme"] == "dark"
        assert cfg["paths"]["data"] == "/proj"
        assert cfg["paths"]["log"] == "/user/logs"
        assert used == [proj_cfg, user_cfg]
