from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

from ebf_core.guards.guards import ensure_not_none


@dataclass(frozen=True)
class UserFileLocator:
    """Locates files in the user's home directory (real or faked for tests)."""
    _override_home: Path | None = None

    @classmethod
    def for_testing(cls, fake_home: Path) -> "UserFileLocator":
        return cls(fake_home.resolve())

    @property
    def home(self) -> Path:
        return (self._override_home or Path.home()).resolve()

    def file(self, *parts: str | Path) -> Path:
        """Absolute path to a file under the user's home directory."""
        return Path(self.home, *parts).expanduser().resolve()

    def try_file(self, *parts: str | Path) -> Path | None:
        """Return the file path if it exists, otherwise None."""
        path = self.file(*parts)
        return path if path.exists() else None


# Global singleton used in production
USER_FILES = UserFileLocator()