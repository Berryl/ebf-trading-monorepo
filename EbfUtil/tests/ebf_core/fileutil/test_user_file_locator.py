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
def sut(temp_user_home: Path) -> UserFileLocator:
    """Standard UserFileLocator instance for testing."""
    return UserFileLocator.for_testing(temp_user_home)


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


class TestUserFileLocator:
    """Tests for the UserFileLocator class."""

    class TestHome:
        """Tests for home directory resolution."""

        def test_home_defaults_to_path_home(self):
            """Without override, home should be Path.home()."""
            locator = UserFileLocator()
            assert locator.home == Path.home().resolve()

        def test_can_override_home_via_for_testing(self, tmp_path):
            """for_testing() should set a custom home directory."""
            locator = UserFileLocator.for_testing(tmp_path)
            assert locator.home == tmp_path.resolve()

        def test_can_override_home_via_constructor(self, tmp_path):
            """Direct constructor call should also allow override."""
            locator = UserFileLocator(tmp_path)
            assert locator.home == tmp_path.resolve()

        def test_home_is_always_resolved(self, tmp_path):
            """Home path should always be absolute and resolved."""
            relative = Path("relative/path")
            locator = UserFileLocator.for_testing(tmp_path / relative)
            assert locator.home.is_absolute()

    class TestFile:
        """Tests for the file() method - constructing paths under home."""

        def test_single_string_part(self, sut, put_file):
            """Should construct a path from a single string part."""
            put_file("config.txt", "content")

            path = sut.file("config.txt")

            assert path.name == "config.txt"
            assert path.parent == sut.home
            assert path.exists()

        def test_multiple_string_parts(self, sut, put_file):
            """Should construct a path from multiple string parts."""
            put_file(".config/app/settings.yaml", "content")

            path = sut.file(".config", "app", "settings.yaml")

            assert path.name == "settings.yaml"
            assert path.parent.name == "app"
            assert path.exists()

        def test_path_object_as_part(self, sut, put_file):
            """Should accept Path objects as parts."""
            put_file("docs/readme.md", "content")

            path = sut.file(Path("docs"), Path("readme.md"))

            assert path.name == "readme.md"
            assert path.exists()

        def test_mixed_string_and_path_parts(self, sut, put_file):
            """Should accept a mix of strings and Path objects."""
            put_file("projects/myapp/config.yml", "content")

            path = sut.file("projects", Path("myapp"), "config.yml")

            assert path.name == "config.yml"
            assert path.exists()

        def test_returns_absolute_resolved_path(self, sut):
            """Result should always be absolute and resolved."""
            path = sut.file("some", "nested", "file.txt")

            assert path.is_absolute()
            # Check it's under home
            assert path.parent.parent.parent == sut.home

        def test_nonexistent_file_returns_path_anyway(self, sut):
            """Should return a path even if the file doesn't exist."""
            path = sut.file("does-not-exist.txt")

            assert path.name == "does-not-exist.txt"
            assert not path.exists()
            # This is expected - file() doesn't check existence

        def test_empty_parts_raises_error(self, sut):
            """Should raise TypeError when called with no parts."""
            with pytest.raises(TypeError, match="missing 1 required positional argument"):
                sut.file()

    class TestTryFile:
        """Tests for the try_file() method - existence-checking variant."""

        def test_returns_path_when_file_exists(self, sut, put_file):
            """Should return a path when the file exists."""
            expected = put_file("existing.txt", "content")

            result = sut.try_file("existing.txt")

            assert result == expected
            assert result.exists()

        def test_returns_none_when_file_missing(self, sut):
            """Should return None when the file doesn't exist."""
            result = sut.try_file("missing.txt")

            assert result is None

        def test_works_with_nested_paths(self, sut, put_file):
            """Should work with nested directory structures."""
            expected = put_file(".config/app/settings.yaml", "content")

            result = sut.try_file(".config", "app", "settings.yaml")

            assert result == expected

        def test_missing_nested_path_returns_none(self, sut, put_file):
            """Should return None for missing nested paths."""
            # Create the parent dir but not the file
            (sut.home / ".config" / "app").mkdir(parents=True)

            result = sut.try_file(".config", "app", "missing.yaml")

            assert result is None

        def test_accepts_path_objects(self, sut, put_file):
            """Should accept Path objects as arguments."""
            expected = put_file("data/export.csv", "content")

            result = sut.try_file(Path("data"), Path("export.csv"))

            assert result == expected


class TestUserFilesGlobalSingleton:
    """Tests for the USER_FILES global singleton."""

    def test_global_singleton_exists(self):
        """USER_FILES should be importable and usable."""
        from ebf_core.fileutil.user_file_locator import USER_FILES

        assert isinstance(USER_FILES, UserFileLocator)
        assert USER_FILES.home == Path.home().resolve()

    def test_global_singleton_is_production_ready(self):
        """USER_FILES should use the real home directory."""
        from ebf_core.fileutil.user_file_locator import USER_FILES

        # Should not have an override
        assert USER_FILES._override_home is None

        # Should point to real home
        path = USER_FILES.file(".bashrc")
        assert path.parent == Path.home().resolve()