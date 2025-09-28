import os
import shutil
from pathlib import Path
from typing import Optional


def find_on_system_path(names: list[str] | None) -> Path | None:
    """
    Return the first executable found by scanning the SYSTEM PATH.

    Deterministic search: iterate `names` in order; for each, scan PATH entries in order.
    If a name is absolute, validate it directly and return if executable.

    Windows:
      - If a name includes an extension (raw.g., "foo.exe"), check it as-is.
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

    return None

def find_start_menu_shortcut(vendor_folders: list[str], patterns: list[str]) -> Path | None:
    """
    Find a Start Menu `.lnk` shortcut under Windows.

    Search order and ranking are deterministic:
    1) APPDATA over PROGRAMDATA
    2) More literal characters in the matched pattern
    3) Fewer wildcards (* or ?)
    4) Longer pattern
    5) Lexicographic path

    Args:
        vendor_folders: Vendor subfolders to search under `.../Start Menu/Programs`.
                        Example: ["Fidelity Investments"]. If empty, search the entire Programs tree.
        patterns: Filename matchers for `.lnk` files. Supports fnmatch wildcards.
                  If a pattern has no wildcards, it is treated as a case-insensitive substring.

    Returns:
        Path to the best matching `.lnk` file, or None if nothing matches or non-Windows.
    """
    import fnmatch
    import os
    from pathlib import Path

    if os.name != "nt":
        return None

    def start_menu_root(env_key: str) -> Path | None:
        base = os.environ.get(env_key)
        if not base:
            return None
        return Path(base) / "Microsoft" / "Windows" / "Start Menu" / "Programs"

    # Prefer user before machine
    roots: list[tuple[int, Path]] = []
    for rank, key in enumerate(("APPDATA", "PROGRAMDATA")):
        r = start_menu_root(key)
        if r and r.exists():
            roots.append((rank, r))
    if not roots:
        return None

    pats = [p.lower() for p in (patterns or [])]
    vendors = vendor_folders or [""]  # empty means search from Programs root

    def match_pattern(name: str) -> str | None:
        if not pats:
            return "*.lnk"
        for pat in pats:
            if ("*" in pat) or ("?" in pat):
                if fnmatch.fnmatch(name, pat):
                    return pat
            else:
                if pat in name:
                    return pat
        return None

    def pat_specificity(pat: str) -> tuple[int, int, int]:
        literal_len = len(pat.replace("*", "").replace("?", ""))  # more is better
        wc = pat.count("*") + pat.count("?")  # fewer is better
        return -literal_len, wc, -len(pat)  # negate so "more/longer" sorts first

    candidates: list[tuple[tuple[int, int, int, int, str], Path]] = []

    for root_rank, root in roots:
        for vendor in vendors:
            base = root if not vendor else (root / vendor)
            if not base.exists():
                continue
            for p in base.rglob("*.lnk"):
                pat = match_pattern(p.name.lower())
                if pat:
                    key = (root_rank, *pat_specificity(pat), str(p).lower())
                    candidates.append((key, p))

    if not candidates:
        return None
    candidates.sort(key=lambda t: t[0])
    return candidates[0][1].resolve()


def find_in_common_roots(globs: list[str]) -> Path | None:
    """
    Search common installation roots with the given glob patterns and return the first match.

    Roots are checked in this order: ProgramFiles, ProgramFiles(x86), LOCALAPPDATA, ProgramData.
    Matching is deterministic: root order first, then lexicographic path among file matches.

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

    candidates: list[tuple[tuple[int, str], Path]] = []
    for ri, root in enumerate(roots):
        for pat in globs:
            for m in root.glob(pat):
                if m.is_file():
                    candidates.append(((ri, str(m).lower()), m))

    if not candidates:
        return None

    candidates.sort(key=lambda x: x[0])
    return candidates[0][1].resolve()


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
]
