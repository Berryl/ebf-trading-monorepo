from pathlib import Path
from typing import Optional, Self


class UserFileLocator:
    """
    Utility for locating files within a user base directory.

    This class is intentionally simple and complements ProjectFileLocator
    without overlapping concerns. It provides:
      - an optional explicit user base dir (useful for tests)
      - fallback to Path.home() when none is set
      - helpers to try locating files underneath that base
    """

    def __init__(self) -> None:
        self._user_base_dir: Optional[Path] = None

    def with_user_base_dir(self, base: Optional[Path]) -> Self:
        """
        Return a new instance with an explicit user base directory.

        Why:
            Tests often need to redirect user-profile paths into a temp folder.
            This isolates the filesystem and avoids touching the real HOME dir.
        """
        clone = UserFileLocator()
        clone._user_base_dir = None if base is None else Path(base).resolve()
        return clone

    @property
    def user_base_dir(self) -> Optional[Path]:
        """Return the explicitly configured base dir, or None if not set."""
        return self._user_base_dir

    def get_user_base_dir(self) -> Path:
        """
        Return the effective user base directory.

        Why:
            If an explicit base is provided (tests), use it.
            Otherwise fall back to the actual user home directory.
        """
        return (self._user_base_dir or Path.home()).resolve()

    def try_get_file_from_user_base_dir(self, filename: str | Path, *subpaths: str | Path) -> Optional[Path]:
        """
        Attempt to resolve a file underneath the user base directory.

        Returns:
            Absolute Path if the file exists, else None.

        Why:
            ConfigService searches both project and user locations.
            This helper supports the user-side lookup without enforcing
            exceptions or existence requirements.
        """
        base = self.get_user_base_dir()
        parts = [base, *(Path(p) for p in subpaths), Path(filename)]
        candidate = Path().joinpath(*parts).resolve()

        return candidate if candidate.exists() else None
