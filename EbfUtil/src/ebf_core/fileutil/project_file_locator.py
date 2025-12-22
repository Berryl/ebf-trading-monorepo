from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from itertools import count
from pathlib import Path
from typing import Optional, Iterable, List, ClassVar, Self

from ebf_core.fileutil.path_norm import norm_path
from ebf_core.guards.guards import ensure_not_empty_str

logger = logging.getLogger(__name__)

_USE_CLASS_DEFAULT = object()  # module-level sentinel (see with_sticky_project_file)


@dataclass(frozen=True)
class ProjectFileLocator:
    """
    Fluent, immutable locator for project roots and project files.

    This class helps locate the root of a project (e.g., where .git lives) and
    construct paths to project files (e.g., config.yaml, pyproject.toml).

    Examples

        Basic usage – auto-detect project root from CWD:
            >>> locator = ProjectFileLocator()
            >>> root = locator.get_project_root()
            >>> # Searches upward from CWD for .git, pyproject.toml, etc.


        Explicit project root:
            >>> locator = ProjectFileLocator().with_project_root(Path("/app"))
            >>> config = locator.get_project_file("config/settings.yaml")
            >>> # Returns: /app/config/settings.yaml

        Sticky project file (for repeated access):
            >>> locator = (ProjectFileLocator().with_project_root(Path("/app")).with_sticky_project_file("config.yaml"))
            >>> config = locator.get_project_file()
            >>> # Returns: /app/config.yaml

        Custom markers for project detection:
            >>> locator = ProjectFileLocator().with_markers(["Cargo.toml", ".git"], priority=".git")
            >>> root = locator.get_project_root()
            >>> # Prefers directories with .git over Cargo.toml

        Per-call override with an absolute path:
            >>> locator = ProjectFileLocator().with_project_root(Path("/app"))
            >>> config = locator.get_project_file("~/shared/config.yaml")
            >>> # Returns: /home/user/shared/config.yaml
    """

    # region Class-level configuration (customize via subclassing or patching)
    DEFAULT_MARKERS: ClassVar[list[str]] = [
        ".git", "pyproject.toml", "requirements.txt", "setup.cfg"
    ]
    DEFAULT_PROJECT_FILE_RELATIVE_PATH: ClassVar[str] = "resources/config.yaml"
    UNLIMITED_DEPTH: ClassVar[int] = -1
    MAX_SEARCH_DEPTH_DEFAULT: ClassVar[int] = 5
    # endregion

    # region Instance configuration (value fields)
    _project_root: Optional[Path] = None
    _markers: Optional[List[str]] = None
    _priority_marker: Optional[str] = None
    _project_file_relpath: Optional[Path] = None

    # endregion

    # region Builder methods (return new instances)

    def with_project_root(self, root: Optional[Path]) -> Self:
        """
        Return a new locator with an explicit project root.

        Sets (or clears) the project root directory. When set, get_project_root()
        will return this path instead of performing marker-based auto-detection.

        Args:
            root: Absolute or relative path to use as the project root, or None to clear.
                  Relative paths are resolved against CWD.

        Returns:
            New ProjectFileLocator instance with updated root

        Examples:
            >>> locator = ProjectFileLocator().with_project_root(Path('/my/project'))
            >>> locator.project_root
            PosixPath('/my/project')

            >>> # Clear the root to re-enable auto-detection
            >>> locator2 = locator.with_project_root(None)
            >>> locator2.project_root is None
            True

        Note:
            This does NOT mutate the instance - a new instance is returned.
        """
        new_root = None if root is None else Path(root).resolve()
        return replace(self, _project_root=new_root)

    def with_cwd_project_root(self) -> Self:
        """
        Return a new locator with the current working directory as the project root.

        Convenience method equivalent to with_project_root(Path.cwd()).

        Returns:
            New ProjectFileLocator with CWD as the project root

        Example:
            >>> locator = ProjectFileLocator().with_cwd_project_root()
            >>> locator.project_root == Path.cwd().resolve()
            True
        """
        return self.with_project_root(Path.cwd())

    def with_markers(
            self,
            markers: Optional[Iterable[str]],
            *,
            priority: Optional[str] = None,
    ) -> Self:
        """
        Return a new locator with custom project root markers.

        Markers are files/directories used to detect the project root during
        upward search (e.g., '.git', 'pyproject.toml'). If a priority marker
        is specified, directories containing it are preferred over those with
        only regular markers.

        Args:
            markers: Iterable of marker filenames, or None to use class defaults.
                     Empty iterables are rejected.
            priority: Optional marker name that takes precedence over others.
                     Must be one of the markers in the list.

        Returns:
            New ProjectFileLocator instance with updated markers

        Raises:
            ValueError: If markers arg is an empty iterable

        Examples:
            >>> # Rust project detection
            >>> locator = ProjectFileLocator().with_markers(['Cargo.toml', '.git'])

            >>> # Prefer .git over other markers
            >>> locator = ProjectFileLocator().with_markers(['.git', 'package.json', 'tsconfig.json'],priority='.git')

            >>> # Reset to defaults
            >>> locator = ProjectFileLocator().with_markers(None)
        """
        new_markers = None if markers is None else list(markers)
        return replace(
            self,
            _markers=new_markers,
            _priority_marker=priority,
        )

    def with_sticky_project_file(
            self,
            relpath: Path | str | object = _USE_CLASS_DEFAULT
    ) -> Self:
        """
        Configure the default project file for this locator.

        Sets a "sticky" default file path that will be used by get_project_file()
        when no per-call path is provided. This is useful when you repeatedly
        access the same project file.

        The path must be relative to the project root - absolute paths and tilde
        expansion are not allowed (use per-call arguments in get_project_file for those).

        Args:
            relpath: One of:
                - Omitted/sentinel: Use DEFAULT_PROJECT_FILE_RELATIVE_PATH
                - None: Clear the sticky default
                - str/Path: Set this relative path (from project root)

        Returns:
            New ProjectFileLocator instance with an updated sticky file path

        Raises:
            AssertionError: If relpath is an empty string
            ValueError: If relpath is absolute, contains ~, or is '.'

        Examples:
            >>> # Use class default
            >>> locator = ProjectFileLocator().with_sticky_project_file()
            >>> locator.project_file_relpath
            PosixPath('resources/config.yaml')

            >>> # Set the custom sticky file
            >>> locator = ProjectFileLocator().with_sticky_project_file('config.toml')
            >>> config = locator.get_project_file() # Uses config.toml

            >>> # Clear sticky file
            >>> locator = locator.with_sticky_project_file(None)
            >>> locator.get_project_file() # Returns None

        Design Note:
            Sticky paths are restricted to relative-only to prevent confusion.
            If you need absolute paths or tilde expansion, use the per-call
            relpath argument in get_project_file() instead.
        """
        if relpath is None:
            return replace(self, _project_file_relpath=None)

        if relpath is _USE_CLASS_DEFAULT:
            rp = Path(self.DEFAULT_PROJECT_FILE_RELATIVE_PATH)
        elif isinstance(relpath, str):
            self._validate_string_path(relpath)
            rp = Path(relpath)
        else:
            rp = Path(relpath)

        self._ensure_relative_path(rp)
        return replace(self, _project_file_relpath=rp)

    # endregion

    # region Query methods

    def get_project_root(
            self,
            *,
            max_search_depth: int = MAX_SEARCH_DEPTH_DEFAULT,
    ) -> Path:
        """
        Get the project root directory.

        Resolution strategy:
          1. If an explicit root is set (via with_project_root), return it
          2. Otherwise, perform upward marker search starting from CWD
          3. Return the first directory containing the priority marker or any marker
          4. If no markers are found, fall back to CWD

        The search always starts from the current working directory. This ensures
        that when this library is used as a dependency (e.g., EbfUtil imported by
        EbfLauncher), it finds the calling project's root, not the library's root.

        Args:
            max_search_depth: Maximum parent levels to ascend during marker search.
                             Use UNLIMITED_DEPTH (-1) for no limit.

        Returns:
            Absolute resolved Path to the project root

        Examples:
            >>> # Auto-detection from CWD
            >>> locator = ProjectFileLocator()
            >>> root = locator.get_project_root()
            >>> # Searches upward from CWD for .git, pyproject.toml, etc.

            >>> # Limited search depth
            >>> root = locator.get_project_root(max_search_depth=3)
            >>> # Only searches 3 levels up from CWD

            >>> # With explicit root, search is skipped
            >>> locator = locator.with_project_root(Path('/app'))
            >>> locator.get_project_root()
            PosixPath('/app')

        Note:
            Marker validation occurs at search time, not during with_markers().
            This allows you to configure markers without triggering immediate validation.
        """
        if self._project_root is not None:
            logger.debug("Returning user provided project root")
            return self._project_root

        markers = self._effective_markers()
        self._validate_markers(markers)

        start = self._detect_start_path()
        logger.debug("Starting marker search for project root from %s", start)

        current = start
        found: Optional[Path] = None

        depth_iter = (
            count() if max_search_depth == self.UNLIMITED_DEPTH
            else range(max_search_depth)
        )

        for _ in depth_iter:
            # Priority marker first
            if self._priority_marker and (current / self._priority_marker).exists():
                found = current.resolve()
                logger.debug("Found priority marker '%s' at %s", self._priority_marker, found)
                break

            # Any marker
            for m in markers:
                if (current / m).exists():
                    found = current.resolve()
                    logger.debug("Found marker '%s' at %s", m, found)
                    break

            if found:
                break

            parent = current.parent
            if parent == current:  # Reached filesystem root
                break
            current = parent

        # Fallback if nothing matched: use start (predictable behavior)
        result = (found or start).resolve()
        return result

    def get_project_file(
            self,
            relpath: Optional[Path | str] = None,
            *,
            must_exist: bool = True,
            restrict_to_root: bool = True,
    ) -> Optional[Path]:
        """
        Resolve a project file path.

        Path Resolution Precedence:
          1. Per-call `relpath` argument (if provided)
          2. Sticky default from with_sticky_project_file()
          3. None (returns None)

        Path Handling:
          - Absolute paths (including ~/ expansion): Used directly
          - Relative paths: Resolved under project root
          - Environment variables: Expanded (e.g., $CONFIG_DIR)
          - Tilde: Expands to user home (not project root)

        Args:
            relpath: Path to the project file. Can be:
                    - Relative: resolved under project root
                    - Absolute: used directly (e.g., ~/config.yaml)
                    - None: use sticky default (if set)
            must_exist: If True, raise FileNotFoundError if the file doesn't exist
            restrict_to_root: If True, prevent relative paths from escaping the project root via navigation using '..'

        Returns:
            Absolute resolved Path to the project file, or None if no path is configured

        Raises:
            FileNotFoundError: If must_exist=True and the file doesn't exist
            ValueError: If restrict_to_root=True and the path escapes the project root

        Examples:
            >>> locator = (ProjectFileLocator().with_project_root(Path('/app')).with_sticky_project_file('config.yaml'))

            >>> # Use sticky default
            >>> locator.get_project_file()
            PosixPath('/app/config.yaml')

            >>> # Override with the per-call relative path
            >>> locator.get_project_file('settings/dev.yaml')
            PosixPath('/app/settings/dev.yaml')

            >>> # Absolute path (bypasses project root)
            >>> locator.get_project_file('~/shared-config.yaml')
            PosixPath('/home/user/shared-config.yaml')

            >>> # Allow non-existent files
            >>> locator.get_project_file('new-config.yaml', must_exist=False)
            PosixPath('/app/new-config.yaml')

            >>> # Prevent escaping project root
            >>> locator.get_project_file('../outside.yaml')
            ValueError: Resolved path escapes project root

            >>> # Allow escaping (use with caution)
            >>> locator.get_project_file('../outside.yaml', restrict_to_root=False)
            PosixPath('/outside.yaml')

        Design Notes:
            - Per-call paths support full expansion (tilde, env vars, absolute)
            - Sticky paths are restricted to relative-only (see with_sticky_project_file)
            - This asymmetry allows flexible ad-hoc queries while keeping defaults simple
        """
        # Choose the source: per-call or sticky
        if relpath is not None:
            source_path = relpath
            is_per_call = True
        else:
            if self._project_file_relpath is None:
                return None
            source_path = self._project_file_relpath
            is_per_call = False

        # Get project root
        root = self.get_project_root()

        # Check if the source is already absolute (before norm_path processing)
        # This matters for restrict_to_root logic
        source_is_absolute = Path(source_path).expanduser().is_absolute()

        # Use norm_path to handle all expansion and resolution
        # For sticky paths: no tilde expansion allowed (already validated)
        # For per-call paths: full expansion enabled
        path = norm_path(
            source_path,
            base=root,
            expand_user=is_per_call,  # Only per-call can use ~
            expand_env=True,
        )

        # Validate that the path is under root if required
        # Note: restrict_to_root only applies to relative paths that were resolved
        # under the project root. Absolute paths (including ~ expansion) bypass this.
        if restrict_to_root and not source_is_absolute:
            if not self._is_within(path, root):
                msg = f"Resolved path escapes project root: {path} (root: {root})"
                logger.debug(msg)
                raise ValueError(msg)

        logger.debug(
            "Using %s project file: %s",
            "sticky" if not is_per_call else "per-call",
            path
        )

        # Existence check
        if must_exist and not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")

        return path

    @property
    def project_root(self) -> Optional[Path]:
        """
        The explicitly configured project root, or None if using auto-detection.

        This property returns the _project_root field directly without performing
        any search or computation. To get the actual project root (with fallback
        to auto-detection), use get_project_root() instead.

        Returns:
            Configured project root path, or None if not explicitly set
        """
        return self._project_root

    @property
    def project_file_relpath(self) -> Optional[Path]:
        """
        The sticky default project file path (relative to the project root).

        Returns the configured default file path set via with_sticky_project_file(),
        or None if no default is configured.

        Returns:
            Relative path to the sticky project file, or None
        """
        return self._project_file_relpath

    # endregion

    # region Helper methods

    def _effective_markers(self) -> List[str]:
        """Get the active marker list (instance override or class default)."""
        return self._markers if self._markers is not None else self.DEFAULT_MARKERS

    @staticmethod
    def _validate_markers(markers: Iterable[str]) -> None:
        """
        Validate that markers list is non-empty and contains valid strings.

        Raises:
            ValueError: If markers arg is empty or contains empty strings
        """
        found_any = False
        for m in markers:
            found_any = True
            ensure_not_empty_str(m, "marker")

        if not found_any:
            raise ValueError("Marker list must not be empty. Provide markers or use defaults.")

    @staticmethod
    def _detect_start_path() -> Path:
        """
        Determine the starting point for upward marker search.

        Always starts from the current working directory (CWD). This ensures that
        when EbfUtil is used as a dependency by other projects (e.g., EbfLauncher),
        the marker search finds the *calling project's* root, not EbfUtil's root.

        This design assumes that applications are run from within their project
        directory, which is the standard convention.

        Returns:
            Absolute path to CWD

        Example:
            If EbfLauncher imports ProjectFileLocator from EbfUtil and runs from
            /app/EbfLauncher/, the search starts at /app/EbfLauncher/ and finds
            EbfLauncher's .git, not EbfUtil's .git.
        """
        return Path.cwd().resolve()

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
        """
        Check if the path is within the root directory.

        Args:
            path: Path to check
            root: Root directory to check against

        Returns:
            True if the path is under root, False otherwise
        """
        try:
            # Python 3.9+: Path.is_relative_to
            return path.is_relative_to(root)  # type: ignore[attr-defined]
        except AttributeError:
            # Fallback for older Python
            try:
                path.relative_to(root)
                return True
            except ValueError:
                return False

    @staticmethod
    def _validate_string_path(str_path: str) -> None:
        """
        Validate a string path for use as the sticky project file.

        Raises:
            AssertionError: If the path is empty
            ValueError: If the path is '.' or starts with ~
        """
        ensure_not_empty_str(str_path, "relpath")
        if str_path == ".":
            raise ValueError("'.' is not allowed as a project file.")
        if str_path.startswith("~"):
            raise ValueError(
                f"~ expansion is not allowed in with_sticky_project_file: {str_path!r}"
            )

    @staticmethod
    def _ensure_relative_path(path: Path) -> None:
        """
        Validate that the path is relative (not absolute or drive-anchored).

        Raises:
            ValueError: If the path is absolute or has a drive/root anchor
        """
        err = "The path must be a *relative* path from the project root."
        if getattr(path, "drive", "") or getattr(path, "root", ""):
            raise ValueError(err)
        if path.is_absolute():
            raise ValueError(err)

    # endregion

    def __repr__(self) -> str:
        """String representation showing key configuration."""
        root = self._project_root or "<auto>"
        file = self._project_file_relpath or "<none>"
        return f"<ProjectFileLocator root={root} file={file}>"