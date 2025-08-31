from pathlib import Path
from typing import Optional, Protocol

from ebfutil.guards import guards as g
from .cfg_merger import ConfigMerger
from .loaders import JsonLoader
from .loaders import TomlLoader
from .loaders import YamlLoader
from ..fileutil import FileUtil


class ConfigFormatLoader(Protocol):
    """
    Protocol that all config format loaders must follow.

    Each loader handles a specific file type (YAML, JSON, TOML, etc.)
    and advertises which filename suffixes it supports.

    Attributes:
        file_types (tuple[str, ...]): The filename suffixes this loader supports.

    Methods:
        supports(self, path: Path) -> bool:
            True if this loader can handle a given path's suffix file type.
        load(self, path: Path) -> dict:
            Load and parse the file into a dict. The dict will be empty if an
            error is encountered or the file has no data.
            Note: This method assumes the file exists. Caller is responsible
            for ensuring the file exists before calling this method.
    """

    file_types: tuple[str, ...]

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
    DEFAULT_FILENAME = "config.yaml"

    def __init__(self, loaders: Optional[list[ConfigFormatLoader]] = None) -> None:
        self._loaders: list[ConfigFormatLoader] = loaders or [YamlLoader(), JsonLoader(), TomlLoader()]

    def load(self, app_name: str, *,
             project_search_path: str | Path | None = "config",
             filename: str | Path | None = DEFAULT_FILENAME,
             user_filename: str | Path | None = None,
             return_sources: bool = False,
             file_util: FileUtil | None = None
             ) -> dict | tuple[dict, list[Path]]:
        """
        Load configuration for the given application.

        Search order:
          1. Project: <project_root>/<project_search_path>/<filename>
          2. User: <user_base>/.config/<app_name>/<user_filename>

        If both exist, the user config is merged over the project config
        (dicts merged deeply, lists/scalars replaced). Missing files are
        skipped without error.

        Args:
            app_name: Application name; used for user config path resolution.
            project_search_path: Optional relative folder inside the project root
                (default: "config").
            filename: file name assumes the same for both project and user file names.
                (default: "config.yaml").
            user_filename: Optional override, i.e., "SallyConfig.yaml"
            return_sources: If True, also return the list of source files loaded
                in the order they were applied.
            file_util: Optional FileUtil instance. In production this is usually
                omitted (a new one will be created). In tests, you can supply a
                preconfigured FileUtil bound to a temporary project root or
                user base directory.

        Returns:
            dict: The merged configuration.
            (dict, list[Path]): If return_sources=True, also return the sources
                used in order.
        """
        g.ensure_not_empty_str(app_name, "app_name")
        assert filename, "filename must be either a Path or non-empty string"
        if user_filename is None:
            user_filename = filename

        fu = file_util or FileUtil()
        sources: list[Path] = []
        cfg: dict = {}

        proj_path = fu.try_get_file_from_project_root(filename, project_search_path or "")
        if proj_path:
            cfg = self._load_any(proj_path)
            sources.append(proj_path)

        user_path = fu.try_get_file_from_user_base_dir(user_filename, Path(".config") / app_name)
        if user_path:
            user_cfg = self._load_any(user_path)
            cfg = self._deep_merge(cfg or {}, user_cfg)
            sources.append(user_path)

        return (cfg, sources) if return_sources else cfg

    @staticmethod
    def _deep_merge(dst: dict, src: dict) -> dict:
        return ConfigMerger.deep(dst, src)

    def _load_any(self, path: Path) -> dict:
        """
        Use the first loader that supports the file path.
        Only one loader is applied; loaders are not combined.
        Returns {} if no loader supports the path.
        """
        ldr: ConfigFormatLoader = self._get_loader_for(path)
        return ldr.load(path) if ldr is not None else {}

    def _get_loader_for(self, path: Path) -> ConfigFormatLoader | None:
        """return the first loader that supports the file path, else done."""
        for ldr in self._loaders:
            if ldr.supports(path):
                return ldr
        return None
