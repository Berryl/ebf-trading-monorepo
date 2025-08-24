# from __future__ import annotations
#
# import shutil
# from pathlib import Path
# from unittest.mock import patch
#
# import pytest
#
# from ebfutil.cfgutil import load_config
# from ebfutil.fileutil.file_util import FileUtil
#
#
# @pytest.fixture(scope="module")
# def fixtures_root() -> Path:
#     return Path(__file__).parent / "fixtures"
#
#
# @pytest.fixture
# def project_root(tmp_path: Path) -> Path:
#     """
#     Simulates a project root folder by wrapping built-in pytest tmp_path fixture.
#     This keeps test code consistent, realistic, and cleaner (instead of writing tmp_path / "project" for every test)
#     """
#     return tmp_path / "project"
#
#
# @pytest.fixture
# def fu(project_root: Path) -> FileUtil:
#     return FileUtil(project_root_override=project_root)
#
#
# @pytest.fixture
# def editable_file(fixtures_root: Path, project_root: Path) -> Path:
#     """
#     Copy a fixture file into the test's temp directory.
#     Ensures parent dirs exist. Returns the destination path.
#     """
#     src = fixtures_root / "basic.yaml"
#     tgt = project_root / "config" / "config.yaml"
#     tgt.parent.mkdir(parents=True, exist_ok=True)
#     shutil.copyfile(src, tgt)
#     return tgt
#
#
# class TestYamlCfgUtil:
#     def test_can_load_basic_yaml(self, fu: FileUtil, editable_file):
#         cfg, used = load_config(
#             app_name="myapp",
#             file_util=fu,
#             search_path="config",
#             filename="config.yaml",
#             return_sources=True,
#         )
#         assert cfg["app"] == "myapp"
#         assert cfg["paths"]["log"] == "/var/app/log"
#         assert used == [editable_file]
#     #
#     # def test_user_yaml_overrides_project_yaml(
#     #         self, fixtures_root: Path, project_root: Path, fu: FileUtil, user_home: Path
#     # ):
#     #     proj_cfg = editable_file(fixtures_root / "basic.yaml", project_root / "config" / "config.yaml")
#     #     user_cfg = editable_file(
#     #         fixtures_root / "with_comments.yaml",
#     #         user_home / ".config" / "myapp" / "config.yaml",
#     #     )
#     #     with patch.object(FileUtil, "get_user_base_dir", return_value=user_home):
#     #         cfg, used = load_config(
#     #             app_name="myapp",
#     #             file_util=fu,
#     #             search_path="config",
#     #             filename="config.yaml",
#     #             return_sources=True,
#     #         )
#     #     assert cfg["theme"] == "dark"
#     #     assert cfg["paths"]["data"] == "/home/user/data"
#     #     assert cfg["paths"]["log"] == "/var/app/log"
#     #     assert used == [proj_cfg, user_cfg]