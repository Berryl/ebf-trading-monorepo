from __future__ import annotations

import os
from pathlib import Path

from ebf_core.miscutil.string_helpers import is_str_valued


def norm_path(value: str | os.PathLike[str] | None = None, *,
              base: Path | None = None,
              expand_env: bool = True,
              expand_user: bool = True,
              require_absolute: bool = False,
              ) -> Path | None:
    """
    Normalize a path.

    Args:
        value: Path-like value to normalize (str, Path, or None)
        base: Base directory for resolving relative paths
        expand_env: Whether to expand environment variables like $HOME
        expand_user: Whether to expand ~ to user's home directory
        require_absolute: If True, raises ValueError for relative paths

    Returns:
        Normalized Path object, or None if the value is None or empty

    Raises:
        ValueError: If require_absolute=True and the path is relative

    Examples:
        >>> norm_path("~/docs/file.txt")
        PosixPath('/home/user/docs/file.txt')

        >>> norm_path("config.yml", base=Path("/app"))
        PosixPath('/app/config.yml')
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
        p = p.expanduser()

    if not p.is_absolute() and base is not None:
        p = (base / p).resolve()

    if require_absolute and not p.is_absolute():
        raise ValueError(f"Path is not absolute: {p}")

    return p
