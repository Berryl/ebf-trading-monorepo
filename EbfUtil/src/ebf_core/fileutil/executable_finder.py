"""
Windows-only utilities for finding installed executables.

This module is intentionally Windows-only. It provides reliable, deterministic
discovery of desktop applications via:
- PATH lookup (with full PATHEXT support)
- Start Menu shortcuts (.lnk)
- Common installation roots (Program Files, etc.)

Cross-platform support is planned for a future major version.
"""

from __future__ import annotations

import fnmatch
import os
import shutil
from pathlib import Path
from typing import Sequence, Optional

if os.name != "nt":
    raise ImportError("executable_finder is Windows-only")

START_MENU_PROGRAMS = ("Microsoft", "Windows", "Start Menu", "Programs")


def start_menu_path(base: str | Path, *relative: str) -> Path:
    """Return the full path to a Start Menu Programs subfolder."""
    return Path(base).joinpath(*START_MENU_PROGRAMS, *relative)


class _ShortcutCandidate:
    """Internal helper for deterministic Start Menu shortcut ranking."""
    __slots__ = ("path", "pattern", "root_rank", "depth")

    def __init__(self, path: Path, pattern: str, root_rank: int):
        self.path = path
        self.pattern = pattern
        self.root_rank = root_rank
        # Number of folder levels under the drive (shallower = better)
        self.depth = len(path.parts) - 1  # -1 because parts[0] is a drive (like C:)

    def score(self) -> tuple:
        p = self.pattern
        has_wildcard = "*" in p or "?" in p
        wildcard_count = p.count("*") + p.count("?")
        return (
            self.root_rank,  # 0 = user (APPDATA), 1 = all-users (PROGRAMDATA)
            has_wildcard,  # an exact match beats any wildcard
            -len(p),  # longer pattern = more specific
            wildcard_count,  # fewer wildcards = more specific
            self.depth,  # prefer shortcuts closer to the Programs root
            str(self.path).lower(),  # stable tie-breaker
        )

    def __lt__(self, other: "_ShortcutCandidate") -> bool:
        return self.score() < other.score()


def find_on_system_path(names: Sequence[str] | None) -> Path | None:
    """
    Return the first executable found by scanning the system PATH.

    Handles PATHEXT correctly on Windows, works with absolute paths,
    and is fully deterministic.
    """
    if not names:
        return None

    path_env = os.environ.get("PATH", "")

    for name in names:
        if not name:
            continue
        name = name.strip().strip('"').strip("'")
        p = Path(name)

        if p.is_absolute():
            # Absolute path given → just validate
            if p.exists() and (os.name == "nt" or os.access(p, os.X_OK)):
                return p.resolve()
            continue

        # Let shutil.which do the heavy lifting (respects PATHEXT)
        hit = shutil.which(name, path=path_env)
        if hit:
            return Path(hit).resolve()

        if os.name == "nt" and os.environ.get("PATHEXT", None) == "":
            # Rare case: PATHEXT is explicitly empty → fall back to defaults
            for directory in path_env.split(os.pathsep):
                if not directory:
                    continue
                for ext in (".COM", ".EXE", ".BAT", ".CMD"):
                    candidate = Path(directory) / f"{name}{ext}"
                    if candidate.exists():
                        return candidate.resolve()

    return None


def find_start_menu_shortcut(vendor_folders: Sequence[str], patterns: Sequence[str], ) -> Path | None:
    """
    Find the best Start Menu .lnk shortcut on Windows.

    Ranking (strictly deterministic):
        1. User Start Menu (APPDATA) over All Users (PROGRAMDATA)
        2. An exact filename match without any wildcard
        3. Longer pattern wins
        4. Fewer wildcards wins
        5. Shallower folder depth wins
        6. Lexicographic path

    Args:
        vendor_folders: Subfolders under Programs to search (e.g. ["Fidelity Investments"]).
                        Empty sequence → search the entire Programs folder.
        patterns: Filename patterns (case-insensitive fnmatch). Empty → any *.lnk

    Returns:
        Resolved Path to the best matching .lnk file (or None).
    """
    if not patterns:
        patterns = ["*.lnk"]

    lowered_patterns = [p.casefold() for p in patterns]
    vendors = [v.strip() for v in vendor_folders] if vendor_folders else [""]

    # Build list of (rank, root_path) — rank 0 = user, rank 1 = all users
    roots: list[tuple[int, Path]] = []
    for rank, env_key in enumerate(("APPDATA", "PROGRAMDATA")):
        base = os.environ.get(env_key)
        if base:
            root = start_menu_path(base)
            if root.exists():
                roots.append((rank, root))

    if not roots:
        return None

    candidates: list[_ShortcutCandidate] = []

    for root_rank, root in roots:
        for vendor in vendors:
            search_root = root if not vendor else root / vendor
            if not search_root.exists():
                continue

            for lnk_path in search_root.rglob("*.lnk"):
                name_cf = lnk_path.name.casefold()
                matched_pattern = next(
                    (pat for pat in lowered_patterns if fnmatch.fnmatch(name_cf, pat)),
                    None,
                )
                if matched_pattern:
                    candidates.append(_ShortcutCandidate(lnk_path, matched_pattern, root_rank))

    if not candidates:
        return None

    winner = min(candidates)
    return winner.path.resolve()


def find_in_common_roots(globs: list[str]) -> Path | None:
    """
    Search common installation roots with the given glob patterns.

    Roots checked in order:
        ProgramFiles → ProgramFiles(x86) → LOCALAPPDATA → ProgramData

    Returns the first matching file (lexicographically earliest per root).
    """
    if not globs:
        return None

    roots = []
    for key in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA", "ProgramData"):
        base = os.environ.get(key)
        if base:
            p = Path(base)
            if p.exists():
                roots.append(p)

    for root in roots:
        for pattern in globs:
            matches = sorted((m for m in root.glob(pattern) if m.is_file()),
                             key=lambda x: str(x).lower())
            if matches:
                return matches[0].resolve()

    return None


def best_of(*candidates: Optional[Path]) -> Path | None:
    """Return the first existing path from the given candidates."""
    for cand in candidates:
        if cand and Path(cand).exists():
            return Path(cand).resolve()
    return None


__all__ = [
    "find_on_system_path",
    "find_start_menu_shortcut",
    "find_in_common_roots",
    "best_of",
    "start_menu_path",
]
