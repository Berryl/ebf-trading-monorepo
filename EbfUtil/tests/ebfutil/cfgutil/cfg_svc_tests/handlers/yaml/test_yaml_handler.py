import re
from pathlib import Path

import pytest
import yaml

from ebfutil.cfgutil import ConfigService
from ebfutil.fileutil import FileUtil
from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class YamlConfigServiceFixture(ConfigServiceFixture):
    @pytest.fixture(scope="class")
    def default_ext(self) -> str:
        return ".yaml"

    @pytest.fixture(scope="class")
    def yaml_cfg_file(self, make_filename) -> str:
        return make_filename()  # "config.yaml"

    @pytest.fixture
    def project_file(self, yaml_cfg_file: str, project_root: Path, project_search_path: str, data: dict) -> Path:
        tgt = project_root / project_search_path / yaml_cfg_file
        tgt.parent.mkdir(parents=True, exist_ok=True)
        tgt.write_text(yaml.safe_dump(data), encoding="utf-8")
        return tgt

    @pytest.fixture
    def project_cfg(self, project_root: Path, make_filename) -> Path:
        return project_root / "config" / make_filename()

    @pytest.fixture
    def user_cfg(self, user_home: Path, app_name: str, make_filename) -> Path:
        return user_home / ".config" / app_name / make_filename()


class TestLoad(YamlConfigServiceFixture):

    def test_can_load_project_config(self, sut: ConfigService, app_name, yaml_cfg_file,
                                     project_file_util, project_file: Path, data: dict
                                     ):
        cfg, sources = sut.load(app_name, filename=yaml_cfg_file, return_sources=True, file_util=project_file_util)

        assert cfg == data
        assert sources == [project_file]
        assert sources[0].name == yaml_cfg_file

    def test_can_load_user_config_when_project_config_absent(
            self, sut: ConfigService, mock_file_util: FileUtil, user_config_factory, app_name: str):
        user_data = {"a": 9, "list": [2], "nest": {"x": 5}}
        user_cfg: Path = user_config_factory(user_data)

        mock_file_util.try_get_file_from_project_root.return_value = None
        mock_file_util.try_get_file_from_user_base_dir.return_value = user_cfg

        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)

        assert cfg == user_data
        assert sources == [user_cfg]

    def test_user_cfg_has_precedence_over_project_cfg(
            self, sut: ConfigService,
            user_config_factory, mock_file_util: FileUtil,
            fake_project_file: Path, app_name: str
    ):
        # project_cfg: {"a": 1, "list": [1], "nest": {"x": 1, "y": 1}}
        # user overrides: list replaced, dict deep-merged
        user_data = {"b": 2, "list": [2], "nest": {"y": 9}}
        user_cfg = user_config_factory(user_data)

        mock_file_util.try_get_file_from_project_root.return_value = fake_project_file
        mock_file_util.try_get_file_from_user_base_dir.return_value = user_cfg

        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)

        assert cfg == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}
        assert sources == [fake_project_file, user_cfg]

    @pytest.mark.parametrize("suffix", ["docx", "blah"])
    def test_unsupported_suffix_yields_empty_dict(
            self, sut: ConfigService, project_file_util, project_root: Path, app_name: str, suffix
    ):
        file_name = f"config.{suffix}"
        p = project_root / "config" / file_name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("key=value\n", encoding="utf-8")

        cfg, sources = sut.load(app_name=app_name, filename=file_name,
                                return_sources=True, file_util=project_file_util)
        assert cfg == {}
        assert sources == [p]


class TestStore(YamlConfigServiceFixture):

    def test_can_store_user_data(
            self, sut: ConfigService, app_name: str,
            mock_file_util: FileUtil, user_home: Path, yaml_cfg_file: str, data: dict
    ):
        mock_file_util.get_user_base_dir.return_value = user_home

        out_path = sut.store(data, app_name, user_filename=yaml_cfg_file, target="user", file_util=mock_file_util)

        expected_path = user_home / ".config" / app_name / yaml_cfg_file
        self._assert_stored_output_path_is(out_path, expected_path)

        persisted = yaml.safe_load(out_path.read_text(encoding="utf-8")) or {}
        assert persisted == data

    def test_store_project_creates_dir_and_writes_yaml(
            self, sut: ConfigService, app_name: str, project_root: Path, yaml_cfg_file: str, data: dict
    ):
        fu = FileUtil(project_root_override=project_root)  # resolves project root to our tmp area

        out_path = sut.store(data, app_name, filename=yaml_cfg_file, target="project", file_util=fu)

        expected_path = project_root / "config" / yaml_cfg_file
        self._assert_stored_output_path_is(out_path, expected_path)

        persisted = yaml.safe_load(out_path.read_text(encoding="utf-8")) or {}
        assert persisted == data

    def test_existing_file_is_overwritten_with_new_content(
            self, sut: ConfigService, app_name: str, mock_file_util: FileUtil, user_home: Path, yaml_cfg_file: str
    ):
        mock_file_util.get_user_base_dir.return_value = user_home

        p = user_home / ".config" / app_name / yaml_cfg_file
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump({"old": 1}), encoding="utf-8")

        # Act: overwrite with new content
        new_data = {"new": 2, "nest": {"k": "v"}}
        out_path = sut.store(new_data, app_name, user_filename=yaml_cfg_file, target="user", file_util=mock_file_util)

        self._assert_stored_output_path_is(out_path, p)
        persisted = yaml.safe_load(out_path.read_text(encoding="utf-8")) or {}
        assert persisted == new_data

    def test_store_unsupported_suffix_raises(
            self, sut: ConfigService, app_name: str, mock_file_util: FileUtil, user_home: Path
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


class TestUpdate(YamlConfigServiceFixture):

    def test_update_merges_deep(
            self, sut: ConfigService, app_name: str,
            mock_file_util: FileUtil, user_home: Path, user_cfg: Path, data: dict,
    ):
        mock_file_util.get_user_base_dir.return_value = user_home

        user_cfg.parent.mkdir(parents=True, exist_ok=True)
        user_cfg.write_text(yaml.safe_dump(data), encoding="utf-8")

        patch = {"b": 2, "list": [2], "nest": {"y": 9}}
        out_path = sut.update(patch, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)

        self._assert_stored_output_path_is(out_path, user_cfg)

        contents = yaml.safe_load(out_path.read_text(encoding="utf-8")) or {}
        # preserves 'a', adds 'b', replaces 'list', and merges 'nest' (keeps x, overrides y).
        assert contents == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}

    def test_update_creates_user_cfg_if_absent(
            self, sut: ConfigService, app_name: str, user_cfg: Path, mock_file_util: FileUtil, user_home: Path,
    ):
        assert not user_cfg.exists()

        mock_file_util.get_user_base_dir.return_value = user_home
        patch = {"k": 1, "nest": {"x": 2}}

        out_path = sut.update(patch, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)

        self._assert_stored_output_path_is(out_path, user_cfg)

        contents = yaml.safe_load(user_cfg.read_text(encoding="utf-8")) or {}
        assert contents == patch

    def test_update_project_merges_deep(
            self,
            sut: ConfigService,
            app_name: str,
            project_root: Path,
            project_file_util: FileUtil,
            yaml_cfg_file: str,
            data: dict,
    ):
        p = project_root / "config" / yaml_cfg_file
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(yaml.safe_dump(data), encoding="utf-8")

        patch = {"b": 2, "list": [2], "nest": {"y": 9}}
        out_path = sut.update(
            patch,
            app_name,
            filename=yaml_cfg_file,
            target="project",
            file_util=project_file_util,
        )

        assert out_path == p
        persisted = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        assert persisted == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}

    def test_update_unsupported_suffix_raises(
            self,
            sut: ConfigService,
            app_name: str,
            mock_file_util: FileUtil,
            user_home: Path,
    ):
        mock_file_util.get_user_base_dir.return_value = user_home
        with pytest.raises(RuntimeError, match=re.escape("No handler available to store files with suffix '.docx'")):
            sut.update(
                {"k": "v"},
                app_name,
                user_filename="config.docx",
                target="user",
                file_util=mock_file_util,
            )
