import os
from pathlib import Path
from typing import Generator, Callable

import pytest

from ebf_core.fileutil.user_file_locator import UserFileLocator


@pytest.fixture
def temp_user_home(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Provides a temporary directory acting as the user's home.
    All files created in tests go under this directory.
    """
    home = tmp_path / "home"
    home.mkdir()
    yield home

@pytest.fixture
def temp_file_setter(temp_user_home: Path) -> Callable:
    """
    Helper to easily create files under the fake home.

    Returns a function: put_file("relative/path.txt", "content") -> Path
    """
    def _put(relative: str | Path, content: str = "") -> Path:
        path = temp_user_home / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path.resolve()

    return _put

@pytest.fixture
def sut_with_home(temp_user_home: Path) -> UserFileLocator:
    return UserFileLocator.for_testing(temp_user_home)

class TestHome:

    def test_home_is_path_home_if_not_overridden(self):
        sut = UserFileLocator()
        assert sut.home == Path.home()


    def test_can_override_home(self, tmp_path):
        sut = UserFileLocator.for_testing(tmp_path)
        expected = tmp_path.resolve()
        assert sut.home == expected

        # THIS WORKS IN PRODUCTION BUT KEEP TESTING CLEAR
        sut = UserFileLocator(tmp_path)
        assert sut.home == expected

    class TestFile:

        def test_parts_cannot_be_none(self, sut_with_home):
            msg = "argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'"

            with pytest.raises(TypeError, match=msg):
                sut_with_home.file(None)

        def test_can_set_with_str(self, sut_with_home, temp_file_setter):
            known_str = "bar.txt"
            temp_file_setter(known_str, "some_content")

            path = sut_with_home.file(known_str)
            assert path.name == known_str

        def test_can_set_with_path(self, sut_with_home, temp_file_setter):
            known_file = temp_file_setter("foo/bar.txt", "some_content")

            path = sut_with_home.file(known_file)
            assert path == known_file

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