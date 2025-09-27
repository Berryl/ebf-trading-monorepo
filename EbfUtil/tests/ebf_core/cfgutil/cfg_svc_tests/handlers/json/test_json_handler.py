import json
import re
from pathlib import Path
from typing import Protocol

import pytest

from ebf_core.cfgutil import ConfigService
from ebf_core.fileutil import ProjectFileLocator
from tests.ebf_core.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class JsonConfigServiceFixture(ConfigServiceFixture):
    @pytest.fixture(scope="class")
    def default_ext(self) -> str:
        return ".json"

    @pytest.fixture(scope="class")
    def json_cfg_file(self, make_filename) -> str:
        return make_filename()  # e.g., "config.json"

    # Explicit JSON writers for seeding
    class ProjectConfigWriter(Protocol):
        def __call__(self, payload: dict, *, file_name: str | None = None, search_path: str = "config") -> Path: ...

    @pytest.fixture
    def project_config_factory(self, project_root: Path, make_filename) -> ProjectConfigWriter:
        def _create(payload: dict, *, file_name: str | None = None, search_path: str = "config") -> Path:
            f = file_name or make_filename(".json")
            p = project_root / search_path / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return p
        return _create

    class UserConfigWriter(Protocol):
        def __call__(self, payload: dict, *, file_name: str | None = None, app: str | None = None) -> Path: ...

    @pytest.fixture
    def user_config_factory(self, user_home: Path, app_name: str, make_filename) -> UserConfigWriter:
        def _create(payload: dict, *, file_name: str | None = None, app: str | None = None) -> Path:
            tgt_app = app or app_name
            f = file_name or make_filename(".json")
            p = user_home / ".config" / tgt_app / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return p
        return _create

    @pytest.fixture
    def project_cfg(self, project_root: Path, make_filename) -> Path:
        return project_root / "config" / make_filename()

    @pytest.fixture
    def user_cfg(self, user_home: Path, app_name: str, make_filename) -> Path:
        return user_home / ".config" / app_name / make_filename()


class TestJsonLoad(JsonConfigServiceFixture):
    def test_can_load_project_config(
        self, sut: ConfigService, app_name, json_cfg_file, project_fu: ProjectFileLocator, project_config_factory, data: dict
    ):
        project_cfg = project_config_factory(data)
        cfg, sources = sut.load(app_name, filename=project_cfg.name, return_sources=True, file_util=project_fu)
        assert cfg == data
        assert sources == [project_cfg]
        assert sources[0].name == json_cfg_file

    def test_can_load_user_config_when_project_config_absent(
        self, sut: ConfigService, mock_file_util: ProjectFileLocator, user_config_factory, app_name: str
    ):
        user_data = {"a": 9, "list": [2], "nest": {"x": 5}}
        user_cfg: Path = user_config_factory(user_data)
        mock_file_util.try_get_file_from_project_root.return_value = None
        mock_file_util.try_get_file_from_user_base_dir.return_value = user_cfg
        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)
        assert cfg == user_data
        assert sources == [user_cfg]

    def test_user_cfg_has_precedence_over_project_cfg(
        self,
        sut: ConfigService,
        user_config_factory,
        project_config_factory,
        mock_file_util: ProjectFileLocator,
        app_name: str,
        data: dict,
    ):
        # seed a real JSON project config
        project_cfg = project_config_factory(data)
        user_data = {"b": 2, "list": [2], "nest": {"y": 9}}
        user_cfg = user_config_factory(user_data)
        mock_file_util.try_get_file_from_project_root.return_value = project_cfg
        mock_file_util.try_get_file_from_user_base_dir.return_value = user_cfg
        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)
        assert cfg == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}
        assert sources == [project_cfg, user_cfg]

    @pytest.mark.parametrize("suffix", ["docx", "blah"])
    def test_unsupported_suffix_yields_empty_dict(
        self, sut: ConfigService, project_fu: ProjectFileLocator, project_config_factory, app_name: str, suffix,
    ):
        file_name = f"config.{suffix}"
        project_cfg = project_config_factory({"k": "v"}, file_name=file_name)
        cfg, sources = sut.load(app_name, filename=file_name, return_sources=True, file_util=project_fu)
        assert cfg == {}
        assert sources == [project_cfg]


class TestJsonStore(JsonConfigServiceFixture):
    def test_can_store_user_data(
        self, sut: ConfigService, app_name: str, mock_file_util: ProjectFileLocator,
            user_home: Path, json_cfg_file: str, data: dict
    ):
        mock_file_util.get_user_base_dir.return_value = user_home
        out_path = sut.store(data, app_name, user_filename=json_cfg_file, target="user", file_util=mock_file_util)
        expected_path = user_home / ".config" / app_name / json_cfg_file
        self._assert_stored_output_path_is(out_path, expected_path)
        persisted = json.loads(out_path.read_text(encoding="utf-8")) or {}
        assert persisted == data

    def test_store_project_creates_dir_and_writes_json(
        self, sut: ConfigService, app_name: str, project_root: Path, json_cfg_file: str, data: dict
    ):
        fu = ProjectFileLocator(project_root_override=project_root)
        out_path = sut.store(data, app_name, filename=json_cfg_file, target="project", file_util=fu)
        expected_path = project_root / "config" / json_cfg_file
        self._assert_stored_output_path_is(out_path, expected_path)
        persisted = json.loads(out_path.read_text(encoding="utf-8")) or {}
        assert persisted == data

    def test_existing_file_is_overwritten_with_new_content(
        self, sut: ConfigService, app_name: str, mock_file_util: ProjectFileLocator, user_home: Path, user_config_factory
    ):
        user_cfg = user_config_factory({"old": 1})
        mock_file_util.get_user_base_dir.return_value = user_home
        new_data = {"new": 2, "nest": {"k": "v"}}
        out_path = sut.store(new_data, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)
        self._assert_stored_output_path_is(out_path, user_cfg)
        persisted = json.loads(out_path.read_text(encoding="utf-8")) or {}
        assert persisted == new_data

    def test_store_unsupported_suffix_raises(
        self, sut: ConfigService, app_name: str, mock_file_util: ProjectFileLocator, user_home: Path
    ):
        mock_file_util.get_user_base_dir.return_value = user_home
        msg = re.escape("No handler available to store files with suffix '.docx'")
        with pytest.raises(RuntimeError, match=msg):
            sut.store(
                cfg={"k": "v"},
                app_name=app_name,
                user_filename="config.docx",
                target="user",
                file_util=mock_file_util,
            )


class TestJsonUpdate(JsonConfigServiceFixture):
    def test_update_merges_deep(
        self, sut: ConfigService, app_name: str, mock_file_util: ProjectFileLocator,
            user_home: Path, user_config_factory, data: dict,
    ):
        user_cfg = user_config_factory(data)
        mock_file_util.get_user_base_dir.return_value = user_home
        patch = {"b": 2, "list": [2], "nest": {"y": 9}}
        out_path = sut.update(patch, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)
        self._assert_stored_output_path_is(out_path, user_cfg)
        contents = json.loads(out_path.read_text(encoding="utf-8")) or {}
        assert contents == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}

    def test_update_creates_user_cfg_if_absent(
        self, sut: ConfigService, app_name: str, user_cfg: Path, mock_file_util: ProjectFileLocator, user_home: Path,
    ):
        assert not user_cfg.exists()
        mock_file_util.get_user_base_dir.return_value = user_home
        patch = {"k": 1, "nest": {"x": 2}}
        out_path = sut.update(patch, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)
        self._assert_stored_output_path_is(out_path, user_cfg)
        contents = json.loads(user_cfg.read_text(encoding="utf-8")) or {}
        assert contents == patch

    def test_update_project_ignores_user_cfg_when_merging(
        self, sut: ConfigService, app_name: str, project_fu: ProjectFileLocator,
            project_config_factory, user_config_factory, data: dict,
    ):
        project_cfg = project_config_factory(data)
        user_config_factory({"a": 999, "nest": {"x": 999}})
        patch = {"b": 2, "list": [2], "nest": {"y": 9}}
        out_path = sut.update(patch, app_name, filename=project_cfg.name, target="project", file_util=project_fu)
        self._assert_stored_output_path_is(out_path, project_cfg)
        contents = json.loads(project_cfg.read_text(encoding="utf-8")) or {}
        assert contents == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}

    def test_update_unsupported_suffix_raises(
        self, sut: ConfigService, app_name: str, mock_file_util: ProjectFileLocator, user_home: Path,
    ):
        mock_file_util.get_user_base_dir.return_value = user_home
        msg = re.escape("No handler available to store files with suffix '.docx'")
        with pytest.raises(RuntimeError, match=msg):
            sut.update({"k": "v"}, app_name, user_filename="config.docx", target="user", file_util=mock_file_util)
