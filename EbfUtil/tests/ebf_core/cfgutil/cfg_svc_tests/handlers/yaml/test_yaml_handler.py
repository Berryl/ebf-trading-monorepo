import re
from pathlib import Path

import pytest
import yaml

from ebf_core.cfgutil import ConfigService
from ebf_core.fileutil import FileUtil
from tests.ebf_core.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


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

    def test_can_load_project_config(
            self, sut: ConfigService, app_name, yaml_cfg_file, project_fu: FileUtil, project_config_factory, data: dict
    ):
        project_cfg = project_config_factory(data)  # writes <project_root>/config/<yaml_cfg_file>

        cfg, sources = sut.load(app_name, filename=project_cfg.name, return_sources=True, file_util=project_fu)

        assert cfg == data
        assert sources == [project_cfg]
        assert sources[0].name == yaml_cfg_file

    def test_can_load_user_config_when_project_config_absent(
            self, sut: ConfigService, mock_file_util: FileUtil, user_config_factory, app_name: str
    ):
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
            self, sut: ConfigService, project_fu: FileUtil, project_config_factory, app_name: str, suffix,
    ):
        file_name = f"config.{suffix}"
        # seed a project file with unsupported suffix
        project_cfg = project_config_factory({"k": "v"}, file_name=file_name)

        cfg, sources = sut.load(app_name, filename=file_name, return_sources=True, file_util=project_fu)
        assert cfg == {}
        assert sources == [project_cfg]


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
            self, sut: ConfigService, app_name: str, mock_file_util: FileUtil, user_home: Path, user_config_factory
    ):
        user_cfg = user_config_factory({"old": 1})  # seed initial user config
        mock_file_util.get_user_base_dir.return_value = user_home

        # overwrite with new content
        new_data = {"new": 2, "nest": {"k": "v"}}
        out_path = sut.store(new_data, app_name, user_filename=user_cfg.name, target="user", file_util=mock_file_util)

        self._assert_stored_output_path_is(out_path, user_cfg)
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
            mock_file_util: FileUtil, user_home: Path, user_config_factory, data: dict,
    ):
        user_cfg = user_config_factory(data)
        mock_file_util.get_user_base_dir.return_value = user_home

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

    def test_update_project_ignores_user_cfg_when_merging(
            self,
            sut: ConfigService,
            app_name: str,
            project_fu: FileUtil,
            project_config_factory,
            user_config_factory,
            data: dict,
    ):
        # seed project config
        project_cfg = project_config_factory(data)

        # seed user config with conflicting values (must NOT be consulted)
        user_config_factory({"a": 999, "nest": {"x": 999}})

        patch = {"b": 2, "list": [2], "nest": {"y": 9}}
        out_path = sut.update(patch, app_name, filename=project_cfg.name, target="project", file_util=project_fu)

        self._assert_stored_output_path_is(out_path, project_cfg)
        contents = yaml.safe_load(project_cfg.read_text(encoding="utf-8")) or {}
        # proves we merged only project+patch; nothing from user cfg leaked in
        assert contents == {"a": 1, "b": 2, "list": [2], "nest": {"x": 1, "y": 9}}

    def test_update_unsupported_suffix_raises(
            self,
            sut: ConfigService,
            app_name: str,
            mock_file_util: FileUtil,
            user_home: Path,
    ):
        mock_file_util.get_user_base_dir.return_value = user_home
        msg = re.escape("No handler available to store files with suffix '.docx'")
        with pytest.raises(RuntimeError, match=msg):
            sut.update(
                {"k": "v"},
                app_name,
                user_filename="config.docx",
                target="user",
                file_util=mock_file_util,
            )


class TestYamlComments(YamlConfigServiceFixture):

    def test_ignores_full_line_and_inline_comments(
            self, sut: ConfigService, project_fu: FileUtil, project_root: Path, app_name: str
    ):
        p = project_root / "config" / "with_comments.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# top comment\n"
            "base: 1  # inline comment\n"
            "nest:\n"
            "  k: v   # another inline comment\n",
            encoding="utf-8",
        )
        cfg = sut.load(app_name=app_name, filename=p.name, file_util=project_fu)
        assert cfg == {"base": 1, "nest": {"k": "v"}}

    def test_commented_out_keys_are_ignored(
            self, sut: ConfigService, project_fu: FileUtil, project_root: Path, app_name: str
    ):
        p = project_root / "config" / "commented_keys.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "a: 1\n"
            "#b: 2\n"
            "nest:\n"
            "  x: 3\n"
            "  #y: 4\n",
            encoding="utf-8",
        )
        cfg = sut.load(app_name=app_name, filename=p.name, file_util=project_fu)
        assert cfg == {"a": 1, "nest": {"x": 3}}

    def test_hash_in_quoted_strings_is_not_a_comment(
            self, sut: ConfigService, project_fu: FileUtil, project_root: Path, app_name: str
    ):
        p = project_root / "config" / "quoted_hash.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            'msg: "value with #hash inside"\n'
            "path: 'C:\\#folder\\file'\n",
            encoding="utf-8",
        )
        cfg = sut.load(app_name=app_name, filename=p.name, file_util=project_fu)
        assert cfg == {"msg": "value with #hash inside", "path": r"C:\#folder\file"}

    def test_list_items_with_inline_comments(
            self, sut: ConfigService, project_fu: FileUtil, project_root: Path, app_name: str
    ):
        p = project_root / "config" / "list_comments.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "nums:\n"
            "  - 1  # one\n"
            "  - 2  # two\n"
            "  # - 3 (disabled)\n",
            encoding="utf-8",
        )
        cfg = sut.load(app_name=app_name, filename=p.name, file_util=project_fu)
        assert cfg == {"nums": [1, 2]}

    def test_update_strips_comments_in_output(
            self, sut: ConfigService, project_fu: FileUtil, project_root: Path, app_name: str
    ):
        # Start with commented YAML
        p = project_root / "config" / "roundtrip_comments.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "a: 1  # keep a\n"
            "nest:\n"
            "  x: 1  # keep x\n"
            "#  y: 0  # disabled\n",
            encoding="utf-8",
        )
        # Patch merges and then writes via handler.store (which won’t preserve comments)
        sut.update({"nest": {"y": 9}}, app_name, filename=p.name, target="project", file_util=project_fu)

        text = p.read_text(encoding="utf-8")
        assert "# keep a" not in text and "# keep x" not in text  # comments are not preserved on writing
        assert yaml.safe_load(text) == {"a": 1, "nest": {"x": 1, "y": 9}}
