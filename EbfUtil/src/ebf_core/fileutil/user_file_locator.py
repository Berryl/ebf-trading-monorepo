from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ebf_core.fileutil.path_norm import norm_path


@dataclass(frozen=True)
class UserFileLocator:
    """
    Locates files within a user's home directory with support for test overrides.

    This class provides a clean interface for constructing paths relative to a user's
    home directory. In production, it uses the system home directory (Path.home()).
    For testing, you can inject a fake home directory to isolate file operations.

    All paths returned are absolute and resolved. Tilde (~) expansion and environment
    variables are supported and will expand relative to the configured home.

    Examples:
        Production usage:
            >>> locator = UserFileLocator()
            >>> config = locator.file('.config', 'myapp', 'settings.yml')
            >>> # Returns: /home/username/.config/myapp/settings.yml

        Testing usage:
            >>> locator = UserFileLocator.for_testing(Path('/tmp/test-home'))
            >>> config = locator.file('.config', 'myapp', 'settings.yml')
            >>> # Returns: /tmp/test-home/.config/myapp/settings.yml

        With tilde expansion (expands to configured home):
            >>> locator = UserFileLocator.for_testing(Path('/tmp/test-home'))
            >>> config = locator.file('~/documents/notes.txt')
            >>> # Returns: /tmp/test-home/documents/notes.txt

        Checking file existence:
            >>> existing = locator.try_file('.bashrc')
            >>> # Returns: Path object if exists, None otherwise

    Attributes:
        _override_home: Optional path override for testing (None uses system home)
    """
    _override_home: Path | None = None

    @classmethod
    def for_testing(cls, fake_home: Path) -> "UserFileLocator":
        """
        Create a UserFileLocator with a custom home directory for testing.

        This factory method creates an instance that uses a fake home directory
        instead of the system home. All path operations will be relative to this
        fake home, allowing tests to run in isolation without touching the real
        filesystem.

        Args:
            fake_home: Path to use as the home directory (will be resolved to absolute)

        Returns:
            UserFileLocator instance configured with the fake home

        Example:
            >>> tmp = Path('/tmp/my-test-home')
            >>> tmp.mkdir(exist_ok=True)
            >>> locator = UserFileLocator.for_testing(tmp)
            >>> locator.home
            PosixPath('/tmp/my-test-home')
        """
        return cls(fake_home.resolve())

    @property
    def home(self) -> Path:
        """
        The configured home directory (absolute and resolved).

        Returns the override home if set (via for_testing), otherwise returns
        the system home directory (Path.home()).

        Returns:
            Absolute, resolved Path to the home directory
        """
        return (self._override_home or Path.home()).resolve()

    def file(self, *parts: str | Path) -> Path:
        """
        Construct an absolute path to a file under the home directory.

        Joins the provided path components and resolves them relative to the
        configured home directory. Supports tilde (~) expansion and environment
        variables, which expand relative to the configured home (not system home).

        The file does not need to exist. Use try_file() if you need existence checking.

        Args:
            *parts: Path components to join (strings or Path objects)
                   Can include ~, environment variables like $VAR, or plain paths
                   At least one part is required.

        Returns:
            Absolute, resolved Path under the home directory

        Raises:
            TypeError: If called with no arguments

        Examples:
            >>> locator = UserFileLocator()
            >>> locator.file('.config', 'app', 'settings.yml')
            PosixPath('/home/user/.config/app/settings.yml')

            >>> locator.file('~/documents/notes.txt')  # ~ expands to home
            PosixPath('/home/user/documents/notes.txt')

            >>> locator.file('$CONFIG_DIR/settings.yml')  # env var expansion
            PosixPath('/home/user/.config/settings.yml')

        Note:
            For testing with a custom home, tilde and env vars expand relative
            to the custom home, not the system home.
        """
        if not parts:
            raise TypeError("file() missing 1 required positional argument: 'parts'")

        path = Path(*parts) if len(parts) > 1 else parts[0]
        return norm_path(path, base=self.home, home=self.home)

    def try_file(self, *parts: str | Path) -> Path | None:
        """
        Construct a path under home directory, returning None if it doesn't exist.

        Similar to file(), but performs an existence check. Returns the resolved
        path if the file exists, otherwise returns None.

        Args:
            *parts: Path components to join (strings or Path objects)

        Returns:
            Absolute Path if the file exists, None otherwise

        Examples:
            >>> locator = UserFileLocator()
            >>> config = locator.try_file('.bashrc')
            >>> if config:
            ...     print(f"Found config at {config}")
            ... else:
            ...     print("Config not found")

            >>> locator.try_file('.config', 'nonexistent', 'file.txt')
            None
        """
        path = self.file(*parts)
        return path if path.exists() else None


# Global singleton used in production
# Use this for application code that works with real user files
USER_FILES = UserFileLocator()