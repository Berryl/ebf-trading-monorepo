from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional

from ebfutil.fileutil.file_util import FileUtil

__all__ = ["load_config", "save_config"]


def load_config(
        app_name: str,
        *,
        file_util: Optional[FileUtil] = None,
        search_path: Optional[str] = None,
        filename: str = "config.yaml",
        return_sources: bool = False,
):
    """
    Load config by deep-merging (lowest→highest):
      1) project root / <search_path>/<filename>
      2) user base   / .config/<app_name>/<filename>    (platform-adjusted)
    YAML is assumed; JSON/TOML may be added later by extension sniffing.

    Returns:
      - dict (or (dict, [Path,...]) if return_sources=True)
    """
    raise NotImplementedError


def save_config(cfg: Mapping, target: Path) -> None:
    """
    Atomically write config to 'target'.
    """
    raise NotImplementedError
