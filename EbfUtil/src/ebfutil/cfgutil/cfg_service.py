from pathlib import Path
from typing import Optional, Protocol

from .loaders import JsonLoader
from .loaders import TomlLoader
from .loaders import YamlLoader
from ..fileutil import FileUtil


class ConfigFormatLoader(Protocol):
    """Contract for all config format loaders for strong typing."""

    suffixes: tuple[str, ...]

    def supports(self, path: Path) -> bool:
        ...

    def load(self, path: Path) -> dict:
        ...


class ConfigService:
    """
    Orchestrates config loading:
      • Finds candidate files (project root, user base).
      • Delegates parsing to format loaders.
      • Merges configs with user overrides taking precedence.
    """

    def __init__(self, loaders: Optional[list[ConfigFormatLoader]] = None) -> None:
        # YAML only for now
        self._loaders: list[ConfigFormatLoader] = loaders or [YamlLoader()]

    @staticmethod
    def _deep_merge(dst: dict, src: dict) -> dict:
        for k, v in src.items():
            if isinstance(v, dict) and isinstance(dst.get(k), dict):
                ConfigService._deep_merge(dst[k], v)
            else:
                dst[k] = v
        return dst

    def _load_any(self, path: Path) -> dict:
        for ldr in self._loaders:
            if ldr.supports(path):
                return ldr.load(path)
        return {}  # unknown suffix → ignore for now

    def load(
        self,
        app_name: str,
        *,
        file_util: Optional[FileUtil] = None,
        search_path: Optional[str] = None,
        filename: str = "config.yaml",
        return_sources: bool = False,
    ) -> dict | tuple[dict, list[Path]]:
        fu = file_util or FileUtil()
        sources: list[Path] = []
        cfg: dict = {}

        proj_root = fu.get_project_root()
        proj_path = proj_root / filename if not search_path else proj_root / search_path / filename
        if proj_path.exists():
            cfg = self._load_any(proj_path)
            sources.append(proj_path)

        user_base = fu.get_user_base_dir()
        user_path = user_base / ".config" / app_name / filename
        if user_path.exists():
            user_cfg = self._load_any(user_path)
            cfg = self._deep_merge(cfg or {}, user_cfg)
            sources.append(user_path)

        return (cfg, sources) if return_sources else cfg