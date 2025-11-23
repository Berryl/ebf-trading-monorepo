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
def put_file(temp_user_home: Path) -> Callable:
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


class TestHome:

    def test_home_is_path_home_if_not_overridden(self):
        sut = UserFileLocator()
        assert sut.home == Path.home().resolve()

    def test_can_override_home(self, tmp_path):
        sut = UserFileLocator.for_testing(tmp_path)
        expected = tmp_path.resolve()
        assert sut.home == expected

        # THIS WORKS IN PRODUCTION BUT KEEP TESTING CLEAR
        sut = UserFileLocator(tmp_path)
        assert sut.home == expected

    class TestFile:

        @pytest.fixture
        def sut(self, temp_user_home: Path) -> UserFileLocator:
            return UserFileLocator.for_testing(temp_user_home)

        def test_parts_cannot_be_none(self, sut):
            msg = "argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'"

            with pytest.raises(TypeError, match=msg):
                sut.file(None)

        def test_can_set_with_str(self, sut, put_file):
            known_str = "bar.txt"
            put_file(known_str, "some_content")

            path = sut.file(known_str)
            assert path.name == known_str

        def test_can_set_with_str_parts(self, sut, put_file):
            put_file("foo/bar.txt", "some_content")

            path = sut.file("foo", "bar.txt")
            assert path.name == "bar.txt"

        def test_can_set_with_path(self, sut, put_file):
            known_file = put_file("foo/bar.txt", "some_content")

            path = sut.file(known_file)
            assert path == known_file

        def test_nonexisting_filename_is_misleading_result(self, sut, put_file):
            path = sut.file("blah")
            assert path.exists() is False

    class TestTryFile:

        @pytest.fixture
        def sut(self, temp_user_home: Path) -> UserFileLocator:
            return UserFileLocator.for_testing(temp_user_home)

        def test_return_is_none_if_parts_leads_to_nonexistent_file(self, sut, put_file):
            assert sut.try_file("blah") is None

        def test_parts_cannot_be_none(self, sut):
            msg = "argument should be a str or an os.PathLike object where __fspath__ returns a str, not 'NoneType'"

            with pytest.raises(TypeError, match=msg):
                sut.try_file(None)

        def test_can_get_with__valid_path(self, sut, put_file):
            known_file = put_file("foo/bar.txt", "some_content")

            path = sut.try_file(known_file)
            assert path == known_file
