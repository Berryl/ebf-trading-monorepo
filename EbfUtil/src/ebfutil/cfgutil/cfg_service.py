from pathlib import Path
from typing import Optional, Protocol, Any, Mapping

from .loaders import JsonLoader
from .loaders import YamlLoader
from .loaders import TomlLoader
from ..fileutil import FileUtil


class ConfigFormatLoader(Protocol):
    """
    Protocol that all config format loaders must follow.

    Each loader handles a specific file type (YAML, JSON, TOML, etc.)
    and advertises which filename suffixes it supports.

    Attributes:
        file_types (tuple[str, ...]): The filename suffixes this loader supports.
        default_file_extension (str): The default file extension for this loader.

    Methods:
        supports(self, path: Path) -> bool:
            True if this loader can handle given path's suffix file type.
        load(self, path: Path) -> dict:
            Load and parse the file into a dict. The dict will be empty if an
            error is encountered or the file has no data.
            Note: This method assumes the file exists. Caller is responsible
            for ensuring the file exists before calling this method.
    """

    file_types: tuple[str, ...]
    default_file_extension: str

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
        self._loaders: list[ConfigFormatLoader] = loaders or [YamlLoader(), JsonLoader, TomlLoader]

    def load(
            self,
            app_name: str,
            *,
            file_util: Optional[FileUtil] = None,
            search_path: Optional[str] = None,
            filename: str = "config.yaml",
            return_sources: bool = False,
    ) -> dict | tuple[dict, list[Path]]:
        """
        Load configuration for the given application.

        Search order:
          1. Project config file: <project_root>/<search_path>/<filename>
          2. User config file: <user_base>/.config/<app_name>/<filename>

        If both exist, the user config is merged over the project config
        (dicts merged deeply, lists/scalars replaced).

        :param app_name: Application name; used for user config path resolution
        :param file_util: Optional FileUtil override to avoid creating one here for project/user path lookups.
        :param search_path: Optional relative folder inside project root (default: none, use FileUtil to find it).
        :param filename: Optional file name (default = "config.yaml").
        :param return_sources: If True, also return the list of source files loaded in order.
        :return:
        """
        ensure_not
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

    @staticmethod
    def _deep_merge(dst: dict, src: dict) -> dict:
        return ConfigMerger.deep(dst, src)

    def _load_any(self, path: Path) -> dict:
        """
        Call the on the loader that supports the path to load and return its results
        Returns an empty dict if no loader supports the path.
        """
        ldr: ConfigFormatLoader = self._get_loader_for(path)
        if ldr is None:
            return {}
        else:
            return ldr.load(path)

    def _get_loader_for(self, path: Path) -> ConfigFormatLoader | None:
        """return the first loader that supports the file path."""
        for ldr in self._loaders:
            if ldr.supports(path):
                return ldr
        return None

    def _default_file_name(self, path: Path, filename: str | None) -> str:
        if not filename:
            if not path.name:
                path = path / 'config'
            if not path.suffix:
                path = path / 'yaml'
        ldr: ConfigFormatLoader = self._get_loader_for(path)
        if ldr is not None:
            return f"config.{ldr.default_file_extension}"
