from __future__ import annotations

import os
from pathlib import Path

from ebf_core.miscutil.string_helpers import is_str_valued


def norm_path(
        value: str | os.PathLike[str] | None,
        *,
        base: Path | None = None,
        home: Path | None = None,
        expand_env: bool = True,
        expand_user: bool = True,
        require_absolute: bool = False,
) -> Path | None:
    # noinspection GrazieInspection
    """
    Normalize a path with configurable expansion and resolution.

    This is the workhorse function for all path normalization in ebf_core. It handles
    environment variable expansion, tilde expansion, base directory resolution, and
    path validation in a single, consistent interface.

    Processing Order:
        1. Return None if the value is None or empty/whitespace
        2. Expand environment variables (if expand_env=True)
        3. Expand tilde to the home directory (if expand_user=True)
        4. Resolve relative paths against the base (if the base is provided and the path is relative)
        5. Validate absoluteness (if arg require_absolute=True)

    Args:
        value: Path to normalize. Can be:
               - None → returns None
               - Empty/whitespace string → returns None
               - A str or os.PathLike → normalized according to options
        base: Base directory for resolving relative paths. If provided and the path
              is relative (after expansion), it will be resolved as (base / path).resolve().
              Absolute paths ignore this parameter.
        home: Custom home directory for tilde expansion. If provided, ~ expands to this
              path instead of Path.home(). Useful for testing or sandboxed environments.
              Note: Only the simple ~ is affected; ~username still uses system expansion.
        expand_env: If True, expand environment variables like $HOME, ${USER}, etc.
                    using os.path.expandvars(). Happens before tilde expansion.
        expand_user: If True, expand ~ to the home directory. Uses custom home if provided,
                     otherwise uses Path.home().
        require_absolute: If True, raise ValueError if the final path is relative.
                         Useful for enforcing absolute paths in configuration.

    Returns:
        Normalized Path object, or None if input was None/empty

    Raises:
        ValueError: If arg require_absolute=True and the resulting path is relative

    Examples:

        Basic usage:
            >>> norm_path("docs/readme.md")
            PosixPath('docs/readme.md')

        Tilde expansion (to system home):
            >>> norm_path("~/Documents/notes.txt")
            PosixPath('/home/user/Documents/notes.txt')

        Custom home for testing:
            >>> norm_path("~/config.yml", home=Path("/tmp/test-home"))
            PosixPath('/tmp/test-home/config.yml')

        Environment variable expansion:
            >>> os.environ['CONFIG_DIR'] = '/etc/myapp'
            >>> norm_path("$CONFIG_DIR/settings.yml")
            PosixPath('/etc/myapp/settings.yml')

        Base directory resolution:
            >>> norm_path("config.yml", base=Path("/app"))
            PosixPath('/app/config.yml')

        Combined expansion and base resolution:
            >>> norm_path("$SUBDIR/file.txt", base=Path("/app"))
            PosixPath('/app/configs/file.txt')  # if SUBDIR='configs'

        Absolute paths ignore base:
            >>> norm_path("/etc/config.yml", base=Path("/app"))
            PosixPath('/etc/config.yml')

        Require absolute paths:
            >>> norm_path("relative/path.txt", require_absolute=True)
            ValueError: Path is not absolute: relative/path.txt

        None and empty handling:
            >>> norm_path(None)
            None
            >>> norm_path("")
            None
            >>> norm_path("   ")
            None

    Design Notes:
        - Empty/whitespace strings are treated as None for convenience
        - Environment expansion happens before tilde to allow $VAR/~/file patterns
        - Custom home only affects simple ~, not ~username (system behavior)
        - Base resolution only applies to relative paths (after all expansion)
        - The function is pure - no side effects or caching

    See Also:
        - UserFileLocator: Uses this with home parameter for user file operations
        - ProjectFileLocator: Uses this with base parameter for project file operations
    """
    if value is None:
        return None

    s = str(value)
    if not is_str_valued(s):
        return None

    # Step 1: Expand environment variables
    if expand_env:
        s = os.path.expandvars(s)

    p = Path(s)

    # Step 2: Expand tilde to the home directory
    if expand_user:
        if home is not None:
            # Custom home: manually replace ~ (but not ~username)
            if str(p).startswith("~"):
                parts = p.parts
                if parts[0] == "~":
                    # Simple ~ → replace with custom home
                    p = Path(home, *parts[1:])
                elif parts[0].startswith("~"):
                    # ~username → fall back to standard system expansion
                    # (can't easily override for other users)
                    p = p.expanduser()
        else:
            # Standard expansion using system home
            p = p.expanduser()

    # Step 3: Resolve relative paths against base
    if not p.is_absolute() and base is not None:
        p = (base / p).resolve()

    # Step 4: Validate absoluteness if required
    if require_absolute and not p.is_absolute():
        raise ValueError(f"Path is not absolute: {p}")

    return p