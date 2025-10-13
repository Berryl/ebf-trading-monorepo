import re
from pathlib import Path
from typing import Protocol

import pytest

from ebf_core.cfgutil import ConfigService
from ebf_core.fileutil import ProjectFileLocator
from tests.ebf_core.support.fixtures.cfg_svc_fixture import ConfigServiceFixture

# Uses current TomlHandler behavior (read-only; store/update unsupported).


class TomlConfigServiceFixture(ConfigServiceFixture):
    @pytest.fixture(scope="class")
    def default_ext(self) -> str:
        return ".toml"

    # --- Minimal TOML writers for seeding (no deps, read-only service) ---
    class ProjectConfigWriter(Protocol):
        def __call__(
            self, payload: dict, *, file_name: str | None = None, search_path: str = "config"
        ) -> Path: ...

    @pytest.fixture
    def project_config_factory(self, project_root: Path, make_filename) -> ProjectConfigWriter:
        def dumps_toml(d: dict) -> str:
            parts: list[str] = []
            for k, v in d.items():
                if isinstance(v, dict):
                    parts.append(f"[{k}]")
                    for k2, v2 in v.items():
                        parts.append(f"{k2} = {v2!r}".replace("'", ""))
                elif isinstance(v, list):
                    parts.append(f"{k} = [{', '.join(map(str, v))}]")
                else:
                    parts.append(f"{k} = {v}")
            return "\n".join(parts) + "\n"

        def _create(payload: dict, *, file_name: str | None = None, search_path: str = "config") -> Path:
            f = file_name or make_filename(".toml")
            p = project_root / search_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            # simple TOML for the known test payloads
            p.write_text(dumps_toml(payload), encoding="utf-8")
            return p

        return _create

    class UserConfigWriter(Protocol):
        def __call__(self, payload: dict, *, file_name: str | None = None, app: str | None = None) -> Path: ...

    @pytest.fixture
    def user_config_factory(self, user_home: Path, app_name: str, make_filename) -> UserConfigWriter:
        def dumps_toml(d: dict) -> str:
            parts: list[str] = []
            for k, v in d.items():
                if isinstance(v, dict):
                    parts.append(f"[{k}]")
                    for k2, v2 in v.items():
                        parts.append(f"{k2} = {v2!r}".replace("'", ""))
                elif isinstance(v, list):
                    parts.append(f"{k} = [{', '.join(map(str, v))}]")
                else:
                    parts.append(f"{k} = {v}")
            return "\n".join(parts) + "\n"

        def _create(payload: dict, *, file_name: str | None = None, app: str | None = None) -> Path:
            tgt_app = app or app_name
            f = file_name or make_filename(".toml")
            p = user_home / ".config" / tgt_app / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(dumps_toml(payload), encoding="utf-8")
            return p

        return _create

    @pytest.fixture
    def project_cfg(self, project_root: Path, make_filename) -> Path:
        return project_root / "config" / make_filename(".toml")

    @pytest.fixture
    def user_cfg(self, user_home: Path, app_name: str, make_filename) -> Path:
        return user_home / ".config" / app_name / make_filename(".toml")


class TestTomlLoad(TomlConfigServiceFixture):
    def test_can_load_project_config(
        self, sut: ConfigService, app_name: str, project_fu: ProjectFileLocator, project_config_factory, data: dict
    ):
        project_cfg = project_config_factory(data)
        cfg, sources = sut.load(app_name, filename=project_cfg.name, return_sources=True, file_util=project_fu)
        assert cfg == data
        assert sources == [project_cfg]

    def test_user_cfg_has_precedence_over_project_cfg(
        self,
        sut: ConfigService,
        app_name: str,
        project_config_factory,
        user_config_factory,
        mock_file_util: ProjectFileLocator,
        data: dict,
    ):
        project_cfg = project_config_factory(data)
        user_data = {"b": 2, "list": [2], "nest": {"y": 9}}
        user_cfg = user_config_factory(user_data)
        mock_file_util.try_get_file_from_project_root.return_value = project_cfg
        mock_file_util.try_get_file_from_user_base_dir.return_value = user_cfg
        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)
        assert cfg == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}
        assert sources == [project_cfg, user_cfg]

    def test_unsupported_suffix_yields_empty_dict(
        self, sut: ConfigService, app_name: str, project_fu: ProjectFileLocator, project_root: Path
    ):
        file_name = "config.docx"
        # create a bogus file so it appears in sources
        p = project_root / "config" / file_name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("garbage", encoding="utf-8")
        cfg, sources = sut.load(app_name, filename=file_name, return_sources=True, file_util=project_fu)
        assert cfg == {}
        assert sources == [p]

    def test_load_ignores_comments(self, sut: ConfigService, app_name: str, project_fu: ProjectFileLocator, project_root: Path):
        p = project_root / "config" / "with_comments.toml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# top comment\n"
            "a = 1  # inline ok\n"
            "list = [1]\n"
            "[nest]\n"
            "x = 1\n"
            "y = 1  # inline\n",
            encoding="utf-8",
        )
        cfg, _ = sut.load(app_name, filename=p.name, return_sources=True, file_util=project_fu)
        assert cfg == {"a": 1, "list": [1], "nest": {"x": 1, "y": 1}}


class TestTomlStore(TomlConfigServiceFixture):
    def test_store_user_raises_not_supported(
        self, sut: ConfigService, app_name: str, mock_file_util: ProjectFileLocator, user_home: Path, user_cfg: Path
    ):
        mock_file_util.get_user_base_dir.return_value = user_home
        msg = re.escape("Writing TOML is not supported by this service.")
        with pytest.raises(RuntimeError, match=msg):
            sut.store({"k": 1}, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)

    def test_store_project_raises_not_supported(
        self, sut: ConfigService, app_name: str, project_root: Path, project_cfg: Path
    ):
        fu = ProjectFileLocator(project_root_override=project_root)
        msg = re.escape("Writing TOML is not supported by this service.")
        with pytest.raises(RuntimeError, match=msg):
            sut.store(cfg={"k": 1}, app_name=app_name, filename=project_cfg.name, target="project", file_util=fu)


class TestTomlUpdate(TomlConfigServiceFixture):
    def test_update_user_raises_not_supported(
        self, sut: ConfigService, app_name: str, mock_file_util: ProjectFileLocator, user_home: Path, user_cfg: Path
    ):
        mock_file_util.get_user_base_dir.return_value = user_home
        msg = re.escape("Writing TOML is not supported by this service.")
        with pytest.raises(RuntimeError, match=msg):
            sut.update({"b": 2}, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)

    def test_update_project_raises_not_supported(
        self, sut: ConfigService, app_name: str, project_root: Path, project_cfg: Path
    ):
        fu = ProjectFileLocator(project_root_override=project_root)
        msg = re.escape("Writing TOML is not supported by this service.")
        with pytest.raises(RuntimeError, match=msg):
            sut.update({"b": 2}, app_name=app_name, filename=project_cfg.name, target="project", file_util=fu)
