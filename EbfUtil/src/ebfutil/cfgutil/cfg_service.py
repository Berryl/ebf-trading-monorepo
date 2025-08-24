from pathlib import Path
from typing import Optional, Protocol, Any, Mapping

from .loaders import YamlLoader
from ..fileutil import FileUtil


class ConfigFormatLoader(Protocol):
    """Contract for all config format loaders for strong typing."""

    suffixes: tuple[str, ...]

    def supports(self, path: Path) -> bool:
        ...

    def load(self, path: Path) -> dict:
        ...


class ConfigMerger:
    """Centralizes deep-merge so behavior stays consistent across callers.

    Why: keep merge logic reusable/testable; src overrides dst.
    Dicts deep-merge; lists/scalars replace.
    """

    @staticmethod
    def deep(dst: dict[str, Any] | None, src: Mapping[str, Any] | None) -> dict[str, Any]:
        if not dst:
            return dict(src or {})
        if not src:
            return dst
        for k, v in src.items():
            if isinstance(v, Mapping) and isinstance(dst.get(k), Mapping):
                dst[k] = ConfigMerger.deep(dict(dst[k]), v)  # type: ignore[arg-type]
            else:
                dst[k] = v
        return dst


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
        return ConfigMerger.deep(dst, src)

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
