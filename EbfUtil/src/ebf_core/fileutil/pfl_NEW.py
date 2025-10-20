# ebf_core/fileutil/project_file_locator.py

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional, Iterable, List, Self

logger = logging.getLogger(__name__)

# Reasonable defaults; adjust to your repos’ conventions as needed.
DEFAULT_MARKERS: List[str] = [
    ".git",
    "pyproject.toml",
    "requirements.txt",
    ".idea",
    ".vscode",
    "setup.cfg",
]

UNLIMITED_DEPTH = -1


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
        2) (not stored) marker search (see get_project_root) — start path detection below.
      Project file:
        per-call argument > instance default `_project_file_relpath` > None

    Start path detection for marker search:
      - If running from an installed package path (contains "site-packages"/"dist-packages"),
        the search starts at `Path.cwd()`. Otherwise we start at `Path(__file__)`.
    """

    # ---------- configuration (value fields) ----------
    _project_root: Optional[Path] = None
    _use_cwd_as_root: bool = False  # retained for API clarity; affects with_project_root(None, use_cwd_as_root=True)
    _markers: Optional[List[str]] = None
    _priority_marker: Optional[str] = None
    _project_file_relpath: Optional[Path] = None

    # ---------- caches (excluded from identity) ----------
    _cached_project_root: Optional[Path] = None
    _cached_project_file: Optional[Path] = None

    # ======== Fluent "builder" methods (return NEW instances) ========

    def with_project_root(self, root: Optional[Path], *, use_cwd_as_root: Optional[bool] = None, ) -> Self:
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

        return replace(
            self,
            _project_root=new_root,
            _use_cwd_as_root=new_flag,
            _cached_project_root=None,
            _cached_project_file=None,
        )

    def with_markers(self, markers: Optional[Iterable[str]], *, priority: Optional[str] = None, ) -> Self:
        """
        Return a new locator with updated project-root markers and optional priority marker.
        """
        new_markers = None if markers is None else list(markers)
        return replace(
            self,
            _markers=new_markers,
            _priority_marker=priority,
            _cached_project_root=None,
            _cached_project_file=None,
        )

    def with_project_file(self, relpath: Optional[Path | str]) -> ProjectFileLocator:
        """
        Return a new locator with a default project file (relative to project root).
        Pass None to clear the default.
        """
        rp = None if relpath is None else Path(relpath)
        return replace(self, _project_file_relpath=rp, _cached_project_file=None)

    # ======== Queries ========

    def get_project_root(self, *, max_search_depth: int = 5, use_cache: bool = True, ) -> Path:
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
            logger.debug("Retuning user provided project root")
            return self._project_root

        if use_cache and self._cached_project_root is not None:
            logger.debug("Retuning cached project root")
            return self._cached_project_root

        markers = self._effective_markers()
        self._validate_markers(markers)

        start = self._detect_start_path()
        logger.debug("Starting marker search for project root")

        current = start
        found: Optional[Path] = None

        depth_iter = range(0, 10 ** 9) if max_search_depth == UNLIMITED_DEPTH else range(max_search_depth)
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
    ) -> Optional[Path]:
        """
        Resolve the project file path.

        Precedence:
          - `relpath` argument on this call
          - instance default `_project_file_relpath`
          - None (returns None)

        Args:
            relpath: Relative path from project root (string or Path-like). If None,
                     the instance default (if any) is used.
            must_exist: If True, raise FileNotFoundError when the resolved file is missing.
            use_cache: If True and no per-call relpath is provided, use/set a tiny cache.

        Returns:
            Absolute resolved Path, or None when no relative path is configured.
        """
        chosen_rel = Path(relpath) if relpath is not None else self._project_file_relpath
        if chosen_rel is None:
            return None

        if use_cache and relpath is None and self._cached_project_file is not None:
            return self._cached_project_file

        root = self.get_project_root(use_cache=use_cache)
        path = (root / chosen_rel).resolve()

        if must_exist and not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")

        if use_cache and relpath is None:
            object.__setattr__(self, "_cached_project_file", path)
        return path

    # ======== Helpers ========

    def _effective_markers(self) -> List[str]:
        return self._markers if self._markers is not None else DEFAULT_MARKERS

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
