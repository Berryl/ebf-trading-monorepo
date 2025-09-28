import os
import shutil
import fnmatch
from pathlib import Path
from typing import Optional, Sequence

START_MENU_PROGRAMS = ("Microsoft", "Windows", "Start Menu", "Programs")

def start_menu_path(base: str | Path, *relative: str) -> Path:
    return Path(base).joinpath(*START_MENU_PROGRAMS, *relative)


def find_on_system_path(names: Sequence[str] | None) -> Path | None:
    """
    Return the first executable found by scanning the SYSTEM PATH.

    Deterministic search: iterate `names` in order; for each, scan PATH entries in order.
    If a name is absolute, validate it directly and return if executable.

    Windows:
      - If a name includes an extension (i.e., "foo.exe"), check it as-is.
      - If no extension, expand PATHEXT (env or default ".COM;.EXE;.BAT;.CMD") in order.
      - Also check os.access(..., X_OK) for symmetry with POSIX.

    POSIX:
      - Require the file to exist and be executable (os.access(..., X_OK)).

    Args:
        names: Candidate executable base names (raw.g., ["foo", "bar"]). If None or empty, returns None.

    Returns:
        Path | None: Resolved path to the first match, or None if nothing is found.
    """
    if not names:
        return None

    path_env = os.environ.get("PATH", "")

    for nm in names:
        if not nm:
            continue
        name = nm.strip().strip('"').strip("'")

        p = Path(name)
        if p.is_absolute():
            if p.exists() and (os.name == "nt" or os.access(p, os.X_OK)):
                return p.resolve()
            continue

        hit = shutil.which(name, path=path_env)
        if hit:
            return Path(hit).resolve()

        # Fallback when PATHEXT is explicitly empty: emulate default extensions.
        if os.name == "nt" and os.environ.get("PATHEXT", None) == "":
            for d in path_env.split(os.pathsep):
                if not d:
                    continue
                for ext in (".COM", ".EXE", ".BAT", ".CMD"):
                    candidate = Path(d) / f"{name}{ext}"
                    if candidate.exists():
                        return candidate.resolve()

    return None

def find_start_menu_shortcut(vendor_folders: Sequence[str], patterns: Sequence[str]) -> Path | None:
    """
    Find a Start Menu `.lnk` shortcut under Windows.

    Ranking (deterministic):
      1) APPDATA over PROGRAMDATA
      2) More literal characters in the matched pattern
      3) Fewer wildcards
      4) Longer pattern
      5) Lexicographic path
    """
    if os.name != "nt":
        return None

    def start_menu_root(env_key: str) -> Path | None:
        env_base = os.environ.get(env_key)
        return start_menu_path(env_base) if env_base else None

    roots: list[tuple[int, Path]] = []
    for rank, key in enumerate(("APPDATA", "PROGRAMDATA")):
        root = start_menu_root(key)
        if root and root.exists():
            roots.append((rank, root))
    if not roots:
        return None

    filters = [s.casefold() for s in (patterns or [])]
    vendors = list(vendor_folders or ("",))  # empty -> search from Programs root

    def match_pattern(name_cf: str) -> str | None:
        if not filters:
            return "*.lnk"  # accept all .lnk when no filters provided
        for pattern in filters:
            if ("*" in pattern) or ("?" in pattern):
                if fnmatch.fnmatch(name_cf, pattern):
                    return pattern
            elif pattern in name_cf:
                return pattern
        return None

    def pattern_specificity(pattern: str) -> tuple[int, int, int]:
        literal_len = len(pattern.replace("*", "").replace("?", ""))  # more is better
        wc = pattern.count("*") + pattern.count("?")  # fewer is better
        return -literal_len, wc, -len(pattern)  # negate so “more/longer” sorts first

    best_key: tuple[int, int, int, int, str] | None = None
    best_path: Path | None = None

    for root_rank, root in roots:
        for vendor in vendors:
            search_root = root if not vendor else (root / vendor)
            if not search_root.exists():
                continue
            for path in search_root.rglob("*.lnk"):
                matched = match_pattern(path.name.casefold())
                if not matched:
                    continue
                key = (root_rank, *pattern_specificity(matched), str(path).lower())
                if best_key is None or key < best_key:
                    best_key, best_path = key, path

    return best_path.resolve() if best_path else None


def find_in_common_roots(globs: list[str]) -> Path | None:
    """
    Search common installation roots with the given glob patterns and return the first match.

    Roots are checked in this order: ProgramFiles, ProgramFiles(x86), LOCALAPPDATA, ProgramData.
    Matching is deterministic: root order first, then lexicographic path among file matches.
    Note: patterns are non-recursive unless you use ** (e.g., "**/*.exe").

    Args:
        globs: Glob patterns relative to each root (e.g., ["**/Fidelity*/Active*Trader*Pro*/**/*.exe"]).

    Returns:
        The resolved Path of the first matching file, or None if no matches are found.
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
        for pat in globs:
            matches = sorted((m for m in root.glob(pat) if m.is_file()), key=lambda x: str(x).lower())
            if matches:
                return matches[0].resolve()
    return None

def best_of(*candidates: Optional[Path]) -> Path | None:
    """
    Return the first existing path from the given candidates (left to right).

    Args:
        candidates: Zero or more Path objects (or None). None/absent paths are skipped.

    Returns:
        The first candidate that exists, resolved to an absolute Path; otherwise None.
    """
    for cand in candidates:
        if not cand:
            continue
        p = Path(cand)
        if p.exists():
            return p.resolve()
    return None

__all__ = [
    "find_on_system_path",
    "find_start_menu_shortcut",
    "find_in_common_roots",
    "best_of",
    "start_menu_path"
]
