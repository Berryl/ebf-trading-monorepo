import logging
import os
from pathlib import Path
from typing import Union

BASE_DIR_STRUCTURE = Path('Dropbox') / 'Green Olive' / 'Investing'

logger = logging.getLogger(__name__)


class FileUtil:
    """
    Helper to locate files used in various investing related projects including
    Office automation desktop, & browser based apps
    """

    def __init__(self, markers: list[str] | None = None, priority_marker: str | None = None):
        self._cached_base_dir = None
        self._cached_project_root = None
        self._common_project_markers: list[str] = markers
        self._priority_marker = priority_marker

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
        for _ in range(max_search_depth):
            if priority_marker and (current_path / priority_marker).exists():
                result = current_path.resolve()
                break

            for marker in effective_markers:  # ← Fixed: use effective_markers
                if (current_path / marker).exists():
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

    @staticmethod
    def _ensure_valid_marker_args(markers, priority_marker):
        if not all(isinstance(m, str) and m.strip() for m in markers):
            raise ValueError("Markers must be non-empty strings")
        if priority_marker and (not isinstance(priority_marker, str) or not priority_marker.strip()):
            raise ValueError("Priority marker must be a non-empty string")

    def get_base_dir(self) -> Path:
        """Returns the base directory, prioritizing project context or user Dropbox."""
        if self._cached_base_dir is None:
            project_base = self.get_project_root() / BASE_DIR_STRUCTURE
            self._cached_base_dir = project_base if project_base.exists() else self.get_default_base()
        return self._cached_base_dir

    def get_file_from_investing(self, file_name: Union[str, Path]) -> Path:
        """Returns the full path to a file within the Investing directory.

        Args:
            file_name: A string or Path object representing the file name or relative path.

        Returns:
            Path: The full path to the requested file.
        """
        if isinstance(file_name, str):
            file_name = Path(file_name)
        full_path = self.get_base_dir() / file_name
        self.ensure_path_exists(full_path, 'Investing')
        return full_path

    def get_file_from_project_root(self, file_name: Union[str, Path], search_path: Union[str, Path] = '') -> Path:
        """Returns the full path to a file within the project root directory, optionally under a specified subdirectory.

        Args:
            file_name: A string or Path object representing the file name or relative path.
            search_path: An optional string or Path object for a subdirectory (default is empty, meaning project root).

        Returns:
            Path: The full path to the requested file.

        Raises:
            FileNotFoundError: If the resulting file does not exist.
        """
        if isinstance(file_name, str):
            file_name = Path(file_name)
        if isinstance(search_path, str):
            search_path = Path(search_path)
        full_path = self.get_project_root() / search_path / file_name
        self.ensure_path_exists(full_path, f"project root{'/' + str(search_path) if search_path else ''}")
        return full_path

    @staticmethod
    def ensure_path_exists(full_path: Path, dir_name: str):
        if not full_path.exists():
            raise FileNotFoundError(f"The file {full_path} does not exist in the {dir_name} directory.")

    @staticmethod
    def get_default_base() -> Path:
        """Fallback to USERPROFILE Dropbox directory."""
        return Path(os.environ.get('USERPROFILE', '')) / BASE_DIR_STRUCTURE

    @staticmethod
    def get_user_specific_path() -> Path:
        """Returns a path adjusted for the current user's Dropbox directory."""
        try:
            username = os.getlogin()
        except OSError:
            username = os.environ.get('USERNAME', 'default')
        return Path(f"C:/Users/{username}") / BASE_DIR_STRUCTURE
