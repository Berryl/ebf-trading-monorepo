from __future__ import annotations

import os
from pathlib import Path

from ebf_core.miscutil.string_helpers import is_str_valued


def norm_path(value: str | os.PathLike[str] | None, *,
              base: Path | None = None,
              home: Path | None = None,
              expand_env: bool = True,
              expand_user: bool = True,
              require_absolute: bool = False,
              ) -> Path | None:
    """
    Normalize a path.

    Args:
        value: Path-like value to normalize (str, Path, or None)
        base: Base directory for resolving relative paths
        home: Custom home directory for tilde expansion (defaults to Path.home())
        expand_env: Whether to expand environment variables like $HOME
        expand_user: Whether to expand ~ to home directory
        require_absolute: If True, raises ValueError for relative paths

    Returns:
        Normalized Path object, or None if the value is None or empty

    Raises:
        ValueError: If the path is relative but 'require_absolute=True'

    Examples:
        >>> norm_path("~/docs/file.txt")
        PosixPath('/home/user/docs/file.txt')

        >>> norm_path("config.yml", base=Path("/app"))
        PosixPath('/app/config.yml')

        >>> # Custom home for testing
        >>> norm_path("~/config.yml", home=Path("/tmp/test-home"))
        PosixPath('/tmp/test-home/config.yml')
    """
    if value is None:
        return None

    s = str(value)
    if not is_str_valued(s):
        return None

    if expand_env:
        s = os.path.expandvars(s)

    p = Path(s)

    if expand_user:
        if home is not None:
            # Custom home: manually replace ~ or ~user
            if str(p).startswith("~"):
                parts = p.parts
                if parts[0] == "~":
                    # just replace ~ with our custom home
                    p = Path(home, *parts[1:])
                elif parts[0].startswith("~"):
                    # ~username -> fall back to standard expansion
                    # (can't easily override for other users)
                    p = p.expanduser()
        else:
            # Standard expansion using Path.home()
            p = p.expanduser()

    if not p.is_absolute() and base is not None:
        p = (base / p).resolve()

    if require_absolute and not p.is_absolute():
        raise ValueError(f"Path is not absolute: {p}")

    return p
