from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from ebfutil.fileutil.file_util import FileUtil


def load_config(
    app_name: str,
    *,
    file_util: Optional[FileUtil] = None,
    search_path: Optional[str] = None,
    filename: str = "config.yaml",
    return_sources: bool = False,
):
    """
    Load a configuration file by searching both the project root and the user base,
    then deep-merging them with **user overrides taking precedence**.

    Search order (lowest → the highest precedence):
      1. <project_root> / <search_path> / <filename>
         - project_root is resolved via FileUtil.get_project_root()
         - search_path is optional (e.g. "config"), defaults to project root directly
      2. <user_base> /.config/<app_name>/<filename>
         - user_base is resolved via FileUtil.get_user_base_dir()
         - provides per-user overrides of project defaults

    Behavior:
      • If a file is missing at any level, it is skipped without error.
      • Files are parsed as YAML (extension is not yet sniffed).
      • Dictionaries are deep-merged; user values override project values.
      • Lists and scalars are replaced entirely at the overriding level.

    :param app_name: Application name, used to build the user config path (~/.config/<app_name>).
    :param file_util: Instance of FileUtil. If not provided, a default FileUtil() is created.
    :param search_path: Subdirectory under project root where config lives (e.g. "config").
    :param filename: Config file name to load.
    :param return_sources: If True, also return the list of files that were successfully loaded.
    :return:
    """
    fu = file_util or FileUtil()
    sources: list[Path] = []
    cfg: dict = {}

    def deep_merge(dst: dict, src: dict) -> dict:
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                deep_merge(dst[k], v)
            else:
                dst[k] = v
        return dst

    def load_yaml(p: Path) -> dict:
        try:
            data = yaml.safe_load(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return {}
        return data or {}

    # project root / <search_path>/<filename>
    proj_root = fu.get_project_root()
    proj_path = proj_root / filename if not search_path else proj_root / search_path / filename
    if proj_path.exists():
        cfg = load_yaml(proj_path)
        sources.append(proj_path)

    # user base / .config/<app_name>/<filename>
    user_base = fu.get_user_base_dir()
    user_path = user_base / ".config" / app_name / filename
    if user_path.exists():
        user_cfg = load_yaml(user_path)
        cfg = deep_merge(cfg or {}, user_cfg)
        sources.append(user_path)

    return (cfg, sources) if return_sources else cfg
