from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def norm_path(value: Any, *,
              base: Path | None = None,
              expand_env: bool = True,
              expand_user: bool = True,
              require_absolute: bool = False,
              ) -> Path | None:
    """
    Normalize a path.

    - Accepts None/"" → None
    - Expands env vars and ~
    - Resolves relative paths against `base` (if provided)
    - Optionally enforces an absolute result (require_absolute)
    """
    if value in (None, ""):
        return None

    s = str(value)
    if expand_env:
        s = os.path.expandvars(s)

    p = Path(s)
    if expand_user:
        p = p.expanduser()

    if not p.is_absolute() and base is not None:
        p = (base / p).resolve()

    if require_absolute and not p.is_absolute():
        raise ValueError(f"Path is not absolute: {p!s}")

    return p
