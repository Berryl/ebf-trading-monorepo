from pathlib import Path

import pytest

from ebf_core.fileutil.user_file_locator import UserFileLocator


@pytest.fixture
def sut() -> UserFileLocator:
    return UserFileLocator()

@pytest.mark.integration
class TestHome:

    def test_home_is_path_home_if_not_overridden(self):
        sut = UserFileLocator()
        assert sut.home == Path.home()


    def test_can_override_home(self, tmp_path):
        sut = UserFileLocator.for_testing(tmp_path)
        expected = tmp_path.resolve()
        assert sut.home == expected
    #
    # def test_arg_of_none_resets_the_base_dir_to_none(self, sut, tmp_path):
    #     c1 = sut.with_base_dir(tmp_path)
    #     assert c1.base_dir is not None
    #
    #     s3 = c1.with_base_dir(None)
    #     assert s3.base_dir is None

    # @pytest.mark.integration
    # class TestGetUserBaseDir:
    #
    #     def test_when_not_set_then_returns_path_home_(self, sut):
    #         expected = Path.home().resolve()
    #         actual = sut.get_user_base_dir()
    #         assert actual == expected
    #
    #     def test_returns_previously_set_dir(self, sut, tmp_path):
    #         locator = sut.with_base_dir(tmp_path)
    #         expected = tmp_path.resolve()
    #         actual = locator.get_user_base_dir()
    #         assert actual == expected
    #
    # @pytest.mark.integration
    # class TestTryGetFileFromUserBaseDir:
    #
    #     def test_returns_none_when_file_missing(self, sut, tmp_path):
    #         locator = sut.with_base_dir(tmp_path)
    #         result = locator.try_get_file_from_user_base_dir("missing.yaml")
    #         assert result is None
    #
    #     def test_can_find_file_in_base_dir(self, sut, tmp_path):
    #         target = tmp_path / "settings.yaml"
    #         target.write_text("x")
    #
    #         locator = sut.with_base_dir(tmp_path)
    #         result = locator.try_get_file_from_user_base_dir("settings.yaml")
    #
    #         assert result == target.resolve()
    #         assert result.is_absolute()
    #
    #     def test_can_find_file_in_subfolder_with_relative_parts(self, sut, tmp_path):
    #         folder = tmp_path / "foo" / "bar"
    #         folder.mkdir(parents=True)
    #         target = folder / "settings.yaml"
    #         target.write_text("x")
    #
    #         locator = sut.with_base_dir(tmp_path)
    #
    #         result = locator.try_get_file_from_user_base_dir(
    #             "settings.yaml", "foo", "bar"
    #         )
    #
    #         assert result == target.resolve()
    #         assert result.is_absolute()
    #
    #     def test_accepts_path_objects_for_filename_and_subpaths(self, sut, tmp_path):
    #         folder = tmp_path / "nested"
    #         folder.mkdir()
    #         target = folder / "config.json"
    #         target.write_text("{}")
    #
    #         locator = sut.with_base_dir(tmp_path)
    #
    #         result = locator.try_get_file_from_user_base_dir(
    #             Path("config.json"), Path("nested")
    #         )
    #
    #         assert result == target.resolve()
    #         assert result.is_absolute()