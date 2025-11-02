# ebf_core/fileutil/project_file_locator.py

from __future__ import annotations

import logging
from dataclasses import dataclass, replace, field
from itertools import count
from pathlib import Path
from typing import Optional, Iterable, List

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ProjectFileLocator:
    """
    Fluent, builder-style locator for project roots and project files.

    Immutability model:
      - Instances are *value objects*. Each `with_*` method returns a **new** instance.
      - Internal caches (_cached_project_root/_cached_project_file) are not part of the
        value identity and may be set internally for performance.

    Precedence:
      Project root:
        1) explicit `_project_root` (set by with_project_root)
        2) (not stored) marker search (see get_project_root) — see the start path detection below.
      Project file:
        per-call argument > instance default `_project_file_relpath` > None

    Start path detection for marker search:
      - If running from an installed package path (contains "site-packages"/"dist-packages"),
        the search starts at `Path.cwd()`. Otherwise, we start at `Path(__file__)`.
    """
    # region Class-level configuration (customize via subclassing or patching)
    DEFAULT_MARKERS: List[str] = field(
        default_factory=lambda: [
            ".git",
            "pyproject.toml",
            "requirements.txt",
            ".idea",
            ".vscode",
            "setup.cfg",
        ]
    )
    DEFAULT_PROJECT_FILE: str = "resources/config.yaml"
    UNLIMITED_DEPTH: int = -1
    MAX_SEARCH_DEPTH_DEFAULT: int = 5
    # endregion

    # region configuration (value fields)
    _project_root: Optional[Path] = None
    _use_cwd_as_root: bool = False  # retained for API clarity; affects with_project_root(None, use_cwd_as_root=True)
    _markers: Optional[List[str]] = None
    _priority_marker: Optional[str] = None
    _project_file_relpath: Optional[Path] = None
    # endregion

    # region caches (excluded from identity)
    _cached_project_root: Optional[Path] = None
    _cached_project_file: Optional[Path] = None

    # endregion

    # region Fluent "builder" methods (return NEW instances)
    def with_project_root(
            self, root: Optional[Path], *, use_cwd_as_root: Optional[bool] = None, ) -> ProjectFileLocator:
        """
        Return a new locator with an explicit project root (or cleared).

        Args:
            root: The absolute (or relative) path to use as project root, or None.
            use_cwd_as_root: If provided, update the sticky flag on the clone.
                If `root is None` and this (or current) flag is True, the clone captures
                `Path.cwd().resolve()` as the explicit root.

        Notes:
            - This DOES NOT mutate the instance. A new instance is returned.
            - Caches are cleared on the clone.
        """
        new_flag = self._use_cwd_as_root if use_cwd_as_root is None else bool(use_cwd_as_root)

        if root is not None:
            new_root = Path(root).resolve()
        elif new_flag:
            new_root = Path.cwd().resolve()
        else:
            new_root = None

        return replace(self, _project_root=new_root, _use_cwd_as_root=new_flag,
                       _cached_project_root=None, _cached_project_file=None, )

    def with_markers(self, markers: Optional[Iterable[str]], *, priority: Optional[str] = None, ) -> ProjectFileLocator:
        """
        Return a new locator with updated project-root markers and optional priority marker.
        """
        new_markers = None if markers is None else list(markers)
        return replace(self, _markers=new_markers, _priority_marker=priority,
                       _cached_project_root=None, _cached_project_file=None, )

    def with_project_file(self, relpath: Optional[Path | str] = DEFAULT_PROJECT_FILE) -> ProjectFileLocator:
        """
        Return a new locator with a default project file (relative to the project root).
        Call without any arg to make "resources/config.yaml" the default (a common best practice).
        Call with None to clear the default.

        Notes:
            - The sticky default must be a path that is *relative* to the project root.
            Use a per-call override in get_project_file(...) if you need an absolute path.
        """
        if relpath is not None:
            relpath = Path(relpath)
            if relpath.is_absolute():
                raise ValueError("Path must be a *relative* path from the project root.")
        return replace(self, _project_file_relpath=relpath, _cached_project_file=None)

    # endregion

    # region Queries
    def get_project_root(self, *, max_search_depth: int = MAX_SEARCH_DEPTH_DEFAULT, use_cache: bool = True, ) -> Path:
        """
        Get the project root directory.

        Resolution order:
          1) If an explicit root is set on this instance, return it.
          2) Otherwise, perform a marker search upward from a detected start:
             - If this module appears to be in site/dist-packages, start at CWD
             - else start at this module's path
             The first directory containing either the "priority" marker or any
             marker from `markers` is returned.

        Args:
            max_search_depth: Maximum parent levels to ascend (UNLIMITED_DEPTH = -1).
            use_cache: Return a cached result when available.

        Returns:
            Absolute resolved Path to the project root, or the best-effort fallback.
        """
        if self._project_root is not None:
            logger.debug("Returning user provided project root")
            return self._project_root

        if use_cache and self._cached_project_root is not None:
            logger.debug("Returning cached project root")
            return self._cached_project_root

        markers = self._effective_markers()
        self._validate_markers(markers)

        start = self._detect_start_path()
        logger.debug("Starting marker search for project root")

        current = start
        found: Optional[Path] = None

        depth_iter = count() if max_search_depth == self.UNLIMITED_DEPTH else range(max_search_depth)
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
            if parent == current:
                break
            current = parent

        # Fallback if nothing matched: use start (common, predictable)
        result = found or start
        if use_cache:
            object.__setattr__(self, "_cached_project_root", result)
        return result

    def get_project_file(
            self,
            relpath: Optional[Path | str] = None,
            *,
            must_exist: bool = True,
            use_cache: bool = True,
            restrict_to_root: bool = True,
    ) -> Optional[Path]:
        """
        Resolve the project file path.

        Precedence:
          - per-call `relpath` argument (absolute or relative)
          - instance default `_project_file_relpath` (must be relative)
          - None (returns None)

        Args:
            relpath: If absolute, it is validated and returned directly.
                     If relative, it is resolved against the project root.
            must_exist: If True, raise FileNotFoundError when the file is missing.
            use_cache: Cache only applies when *no* per-call relpath is provided.
            restrict_to_root: If True, relative paths that resolve *outside*
                              the project root raise ValueError.

        Returns:
            Absolute resolved Path, or None if no path is configured.
        """
        # Choose the spec
        chosen_rel = Path(relpath) if relpath is not None else self._project_file_relpath
        if chosen_rel is None:
            return None

        # Cache only for the sticky default (no per-call relpath)
        if use_cache and relpath is None and self._cached_project_file is not None:
            logger.debug("Returning cached project file: %s", self._cached_project_file)
            return self._cached_project_file

        # Absolute per-call override: validate and return
        if relpath is not None and chosen_rel.is_absolute():
            path = chosen_rel.resolve()
            logger.debug("Using per-call absolute project file: %s", path)
            if must_exist and not path.exists():
                raise FileNotFoundError(f"Project file not found: {path}")
            return path

        # Otherwise resolve against root
        root = self.get_project_root(use_cache=use_cache)
        path = (root / chosen_rel).resolve()

        if restrict_to_root and not self._is_within(path, root):
            raise ValueError(f"Resolved path escapes project root: {path} (root: {root})")

        if relpath is None:
            logger.debug("Using sticky project file from instance default: %s", path)
        else:
            logger.debug("Using per-call relative project file: %s", path)

        if must_exist and not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")

        if use_cache and relpath is None:
            object.__setattr__(self, "_cached_project_file", path)
        return path

    # endregion

    # region Helpers
    def _effective_markers(self) -> List[str]:
        return self._markers if self._markers is not None else self.DEFAULT_MARKERS

    @staticmethod
    def _validate_markers(markers: Iterable[str]) -> None:
        if not markers:
            raise ValueError("Marker list must not be empty. Provide markers or use defaults.")

    @staticmethod
    def _detect_start_path() -> Path:
        """
        Decide where to start the upward marker search from.

        Logic:
          - If this file looks like it's inside site/dist-packages (installed package),
            start from CWD (so consumers like EbfLauncher are detected).
          - Otherwise, start from this module's file location.
        """
        try:
            here = Path(__file__).resolve()
        except NameError:
            here = Path.cwd().resolve()

        parts_lower = {p.lower() for p in here.parts}
        if "site-packages" in parts_lower or "dist-packages" in parts_lower:
            return Path.cwd().resolve()
        return here.parent  # start from the module’s directory

    @staticmethod
    def _is_within(path: Path, root: Path) -> bool:
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
    # endregion

    # region overrides
    def __repr__(self) -> str:
        root = self._project_root or "<auto>"
        file = self._project_file_relpath or "<none>"
        return f"<ProjectFileLocator root={root} file={file}>"
    # endregion
