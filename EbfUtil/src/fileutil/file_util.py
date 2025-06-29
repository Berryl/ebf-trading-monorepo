import logging
import os
from pathlib import Path
from typing import Union

BASE_DIR_STRUCTURE = Path('Dropbox') / 'Green Olive' / 'Investing'

logger = logging.getLogger(__name__)


class FileUtil:
    """
    Utility for locating files in projects.

    Supports *two clear resolution strategies*:

    1. Project-root-based:
       - Uses either a marker search or explicit override to locate the project root.
       - Resolves base_structure relative to that root. This is typical but not limited to testing files

    2. User based:
       - Always resolves to USERPROFILE + base_structure.
       - Ignores project root or markers entirely.
       - This is typical of production files used outside any python project

    Example usage:

        # For project-local files:
        util.get_file_from_project_root_base("TestingWb.xlsm")

        # For user-based files:
        util.get_file_from_user_base("Dev/constants.xlsm")
    """

    def __init__(
            self,
            base_structure: Path | None = None,
            markers: list[str] | None = None,
            priority_marker: str | None = None,
            project_root_override: Path | None = None
    ):
        """
        Initialize FileUtil.

        Args:
            base_structure: Optional override for the standard Investing path.
                noteL: different base structures should use different FileUtil instances
            markers: Optional list of files/directories that indicate project root.
            priority_marker: Optional single marker to prioritize.
            project_root_override: Explicit path to force as project root.
         """
        self.base_structure = base_structure or BASE_DIR_STRUCTURE
        self._cached_project_root = None
        self._common_project_markers: list[str] = markers
        self._priority_marker = priority_marker
        self._project_root_override = project_root_override

    def set_project_root_override(self, root_override_path: Path):
        """
        Explicitly set the project root for this instance, overriding a marker search.

        Use this when your consuming project has a known root you want all
        resolution to be relative to.

        Example:
            util.set_project_root_override(Path(__file__).parent.parent)

        Args:
            root_override_path: The path to treat as the project root.
        """
        self._project_root_override = root_override_path

    @property
    def common_project_markers(self) -> list[str]:
        if self._common_project_markers is None:
            self._common_project_markers = [
                '.idea',  # PyCharm/IntelliJ
                '.git',  # Git repository
                'pyproject.toml',  # Modern Python projects
                'setup.py',  # Traditional Python packages
                'Pipfile',  # Pipenv projects
                'poetry.lock',  # Poetry projects
                'requirements.txt',  # Common in many Python projects
                'Makefile',  # Build system
                '.vscode'  # VS Code workspace
            ]
        return self._common_project_markers

    def get_project_root(self,
                         markers: list[str] | None = None,
                         use_cache: bool = True,
                         priority_marker: str | None = None,
                         max_search_depth: int = 5
                         ) -> Path:
        """
        Get the project root by ascending until any project marker is found.

        The method searches upward from the current file's directory, checking for
        project markers at each level. If a priority_marker is specified, it's
        checked first at each level before checking the general markers list.

        Args:
            markers: Optional list of files/directories that indicate a project root.
                    If None, uses common_project_markers property.
            use_cache: If True, caches and reuses results for identical parameter sets.
                      Set to False when markers might change between calls.
            priority_marker: Optional single marker to check first at each directory level.
                            Useful for prioritizing .git over requirements.txt, etc.
            max_search_depth: Maximum number of parent directories to search before giving up.
                             Default is 5 levels up from the current file.
                             # Add: "Set to -1 for unlimited search (use cautiously)"

        Returns:
            Path to the project root directory. Falls back to the directory
            containing this file if no markers are found.

        Raises:
            ValueError: If markers contain empty strings or priority_marker is invalid.

        Examples:
            >>> # Use default markers
            >>> file_util = FileUtil()
            >>> root = file_util.get_project_root()

            >>> # Prioritize Git repositories
            >>> root = file_util.get_project_root(priority_marker='.git')

            >>> # Custom markers without caching
            >>> root = file_util.get_project_root(markers=['.my_marker'], use_cache=False)
        """
        if self._project_root_override is not None:
            logger.debug(f"Using override project root: {self._project_root_override}")
            return Path(self._project_root_override).resolve()

        if use_cache and markers is None and priority_marker is None and self._cached_project_root is not None:
            logger.debug(f"Using cached project root: {self._cached_project_root}")
            return self._cached_project_root

        effective_markers = markers or self.common_project_markers
        logger.debug(f"Searching with markers: {effective_markers}")

        if priority_marker is None:
            priority_marker = self._priority_marker

        self._ensure_valid_marker_args(effective_markers, priority_marker)

        try:
            current_path = Path(__file__).resolve()
        except NameError:
            current_path = Path.cwd()
            logger.warning("__file__ not available, using current working directory")

        logger.debug(f"Searching for project root starting from: {current_path}")

        result = None
        search_range = range(100) if max_search_depth == -1 else range(max_search_depth)
        for _ in search_range:
            if priority_marker and (current_path / priority_marker).exists():
                logger.debug(f"Found priority marker '{priority_marker}' at: {current_path}")
                result = current_path.resolve()
                break

            for marker in effective_markers:
                if (current_path / marker).exists():
                    logger.debug(f"Found marker '{marker}' at: {current_path}")
                    result = current_path.resolve()
                    break

            if result:
                break

            parent_path = current_path.parent
            if parent_path == current_path:
                # Reached filesystem root
                break
            current_path = parent_path

        if result:
            if use_cache:
                self._cached_project_root = result
            return result

        # Safe fallback that handles NameError
        try:
            fallback = Path(__file__).resolve().parent
        except NameError:
            fallback = Path.cwd()

        logger.warning(f"No project markers found; falling back to: {fallback}")
        return fallback

    def get_file_from_project_root(
            self,
            file_name: Union[str, Path],
            search_path: Union[str, Path] = ""
    ) -> Path:
        """
        Resolves a file path relative to the project root.

        Example:
            get_file_from_project_root("my file.txt", search_path="tests/data")

        Equivalent to:
            project_root / search_path / file_name

        Raises:
            FileNotFoundError if the resulting file does not exist.
        """
        if isinstance(file_name, str):
            file_name = Path(file_name)
        if isinstance(search_path, str):
            search_path = Path(search_path)

        full_path = self.get_project_root() / search_path / file_name
        self._ensure_path_exists(full_path, f"project root{'/' + str(search_path) if search_path else ''}")
        return full_path

    def get_user_base_dir(self) -> Path:
        """
        Returns the user's base structure directory path.
        """
        return self.get_user_specific_path()

    def get_file_from_user_base(self, file_name: Union[str, Path]) -> Path:
        """
        Resolves a file path inside the user's base structure directory.
        This ignores the project root entirely.

        Raises:
            FileNotFoundError if the file does not exist.
        """
        return self._resolve_file_in_dir(self.get_user_base_dir(), file_name)

    def _resolve_file_in_dir(self, base: Path, file_name: Union[str, Path]) -> Path:
        if isinstance(file_name, str):
            file_name = Path(file_name)
        full_path = base / file_name
        self._ensure_path_exists(full_path, base.name)
        return full_path

    def get_user_specific_path(self) -> Path:
        """
        Returns the full path for the user's base_structure location.
        """
        try:
            username = os.getlogin()
        except OSError:
            username = os.environ.get('USERNAME', 'default')
        return Path(f"C:/Users/{username}") / self.base_structure

    @staticmethod
    def _ensure_valid_marker_args(markers, priority_marker):
        if not all(isinstance(m, str) and m.strip() for m in markers):
            raise ValueError("Markers must be non-empty strings")
        if priority_marker and (not isinstance(priority_marker, str) or not priority_marker.strip()):
            raise ValueError("Priority marker must be a non-empty string")

    @staticmethod
    def _ensure_path_exists(full_path: Path, dir_name: str):
        if not full_path.exists():
            root = full_path.parents[-3] if len(full_path.parents) > 2 else 'N/A'
            msg = f"The file {full_path} does not exist in the {dir_name} directory. Searched from project root: {root}"
            raise FileNotFoundError(msg)
