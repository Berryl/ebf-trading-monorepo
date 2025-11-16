from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from itertools import count
from pathlib import Path
from typing import Optional, Iterable, List, ClassVar, Self

from ebf_core.guards.guards import ensure_not_empty_str

logger = logging.getLogger(__name__)

_USE_CLASS_DEFAULT = object()  # module-level sentinel (see with_project_file)


@dataclass(frozen=True)
class ProjectFileLocator:
    """
    Fluent, builder-style locator for project roots and project files.

    Immutability model:
      - Instances are *value objects*. Each `with_*` method returns a **new** instance.
      - Internal caches (_cached_project_root/_cached_project_file) are not part of the
        value identity and may be set internally for performance.
        NOTE: this is not thread safe and counter-intuitive.to being truly frozen.

    Precedence:
      Project root:
        1) explicit `_project_root` (set by with_project_root)
        2) (not stored) marker search (see get_project_root) — see the start path detection below.
      Project file:
        per-call argument > instance default `_project_file_relpath` > None

    Start path detection for marker search:
      - If running from an installed package path (contains "site-packages"/"dist-packages"),
        the search starts at `Path.cwd()`. Otherwise, we start at the module’s directory.
    """

    # region Class-level configuration (customize via subclassing or patching)
    DEFAULT_MARKERS: ClassVar[list[str]] = [
        ".git", "pyproject.toml", "requirements.txt", "setup.cfg"
    ]
    DEFAULT_PROJECT_FILE_RELATIVE_PATH: ClassVar[str] = "resources/config.yaml"
    UNLIMITED_DEPTH: ClassVar[int] = -1
    MAX_SEARCH_DEPTH_DEFAULT: ClassVar[int] = 5
    # endregion

    # region configuration (value fields)
    _project_root: Optional[Path] = None
    _markers: Optional[List[str]] = None
    _priority_marker: Optional[str] = None
    _project_file_relpath: Optional[Path] = None
    # endregion

    # region caches (excluded from identity)
    _cached_project_root: Optional[Path] = None
    _cached_project_file: Optional[Path] = None

    # endregion

    # region Fluent "builder" methods (return NEW instances)
    def with_project_root(self, root: Optional[Path]) -> Self:
        """
        Return a new locator with an explicit project root (or cleared).

        Args:
            root: The absolute (or relative) path to use as project root, or None.

        Notes:
            - This DOES NOT mutate the instance. A new instance is returned.
            - Caches are cleared on the clone.
        """
        new_root = None if root is None else Path(root).resolve()

        return replace(self, _project_root=new_root, _cached_project_root=None, _cached_project_file=None, )

    def with_cwd_project_root(self) -> Self:
        return self.with_project_root(Path.cwd())


    def with_markers(self, markers: Optional[Iterable[str]], *, priority: Optional[str] = None, ) -> Self:
        """
        Return a new locator with updated project-root markers and optional priority marker.
        """
        new_markers = None if markers is None else list(markers)
        return replace(self, _markers=new_markers, _priority_marker=priority,
                       _cached_project_root=None, _cached_project_file=None, )

    def with_project_file(self, relpath: Path | str | object = _USE_CLASS_DEFAULT) -> Self:
        """
        Return a new locator with a sticky project file relative to the project root (using relpath).

        Args
            relpath:
            - DEFAULT_PROJECT_FILE_RELATIVE_PATH if arg omitted
            - None: clear the sticky default
            - Path/str: set that *relative* path
        """
        if relpath is None:
            return replace(self, _project_file_relpath=None, _cached_project_file=None)

        if relpath is _USE_CLASS_DEFAULT:
            rp = Path(self.DEFAULT_PROJECT_FILE_RELATIVE_PATH)

        elif isinstance(relpath, str):
            self._validate_string_path(relpath)
            rp = Path(relpath)
        else:
            rp = Path(relpath)

        self._ensure_relative_path(rp)
        return replace(self, _project_file_relpath=rp, _cached_project_file=None)

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

    def get_project_file(self, relpath: Optional[Path | str] = None, *,
                         must_exist: bool = True, use_cache: bool = True, restrict_to_root: bool = True,
                         ) -> Optional[Path]:
        """
        Resolve the project file path.

        Precedence:
          - per-call there is a `relpath` argument (absolute or relative, with ~ expansion)
            NOTE: per-call args do NOT  updates sticky defaults. It's more useful to use this as
            an override of the cache
          - instance 'sticky' default `_project_file_relpath` (must be relative, no ~)
          - None (returns None)

        Args:
            relpath: If provided, expanded with ~, then:
                     - If absolute → used directly
                     - If relative → resolved under project root
            must_exist: Raise FileNotFoundError if the path does not exist.
            use_cache: Cache result when using sticky default.
            restrict_to_root: Prevent relative paths from escaping the project root.

        Returns:
            Absolute resolved Path, or None.
        """
        # Choose the source: per-call or sticky
        if relpath is not None:
            source_path = Path(relpath).expanduser()
            is_per_call = True
        else:
            if self._project_file_relpath is None:
                return None
            source_path = self._project_file_relpath
            is_per_call = False

        # Cache hit: sticky default only
        if use_cache and not is_per_call and self._cached_project_file is not None:
            logger.debug("Returning cached project file: %s", self._cached_project_file)
            return self._cached_project_file

        # Resolve path
        if source_path.is_absolute():
            # Only per-call may be absolute (e.g., from ~)
            if not is_per_call:
                raise ValueError("Sticky project file path cannot be absolute")
            path = source_path.resolve()
            logger.debug("Using per-call absolute project file: %s", path)
        else:
            # Relative: resolve under the project root
            root = self.get_project_root(use_cache=use_cache)
            path = (root / source_path).resolve()

            if restrict_to_root and not self._is_within(path, root):
                msg = f"Resolved path escapes project root: {path} (root: {root})"
                logger.debug(msg)
                raise ValueError(msg)

            logger.debug("Using %s project file: %s", "sticky" if not is_per_call else "per-call relative", path)

        # Existence check
        if must_exist and not path.exists():
            if isinstance(relpath, str) and relpath.startswith("~"):
                    raise ValueError(f"Cannot use ~ expansion and existence check: {relpath!r}")
            raise FileNotFoundError(f"Project file not found: {path}")

        # Cache sticky result
        if use_cache and not is_per_call:
            object.__setattr__(self, "_cached_project_file", path)

        return path

    @property
    def project_root(self) -> Optional[Path]:
        return self._project_root

    @property
    def project_file_relpath(self) -> Optional[Path]:
        return self._project_file_relpath

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

    @staticmethod
    def _validate_string_path(str_path: str) -> None:
        ensure_not_empty_str(str_path, "relpath")
        if str_path == ".":
            s = f"'.' is not allowed as a project file."
            raise ValueError(s)
        if str_path.startswith("~"):
            s = "~ expansion is not allowed in with_project_file."
            raise ValueError(f"{s}: {str_path!r}")

    @staticmethod
    def _ensure_relative_path(path: Path) -> None:
        err = "The path must be a *relative* path from the project root."
        if getattr(path, "drive", "") or getattr(path, "root", ""):
            raise ValueError(err)
        if path.is_absolute():
            raise ValueError(err)

    # endregion

    # region overrides
    def __repr__(self) -> str:
        root = self._project_root or "<auto>"
        file = self._project_file_relpath or "<none>"
        return f"<ProjectFileLocator root={root} file={file}>"
    # endregion
