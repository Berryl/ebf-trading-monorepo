from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal, Optional

from ebf_core.guards import guards as g

from ..fileutil import ProjectFileLocator
from .cfg_merger import ConfigMerger
from .handlers import JsonHandler, TomlHandler, YamlHandler
from .handlers.cfg_format_handler import ConfigFormatHandler


class ConfigService:
    """
    Orchestrates configuration management:
      • Finds candidate files (project root, user base).
      • Delegates parsing to format handlers.
      • Merges configs with user overrides taking precedence.
    """

    def __init__(self, handlers: Optional[list[ConfigFormatHandler]] = None) -> None:
        self._handlers: list[ConfigFormatHandler] = handlers or [YamlHandler(), JsonHandler(), TomlHandler()]

    def load(self, *paths: Path, return_sources: bool = False) -> dict | tuple[dict, list[Path]]:
        """
        Load and merge configuration files from the given paths, in order.

        Missing paths are silently skipped.
        Later files override earlier ones via deep-merge.
        If return_sources=True, returns (cfg, sources) where `sources`
        is the list of existing files actually applied, in order.

        Why:
            Separates config *discovery* from config *loading*, letting
            callers use ProjectFileLocator / UserFileLocator (or anything)
            to decide which paths to provide.
        """

        merged: dict = {}
        sources: list[Path] = []

        for path in paths:
            if not isinstance(path, Path):
                raise TypeError(f"Expected Path, got {type(path)}: {path!r}")

            if path.exists():
                handler = self._get_handler_for(path)
                if handler is None:
                    # No loader for this file type: skip silently
                    continue

                data = handler.load(path) or {}
                merged = ConfigMerger.deep(merged, data)
                sources.append(path)

        if return_sources:
            return merged, sources
        return merged

    def store(
            self,
            cfg: Mapping[str, Any],
            app_name: str,
            *,
            project_search_path: str | Path = "config",
            filename: str | Path = "config.yaml",
            user_filename: str | Path | None = None,
            target: Literal["project", "user"] = "user",
            file_util: ProjectFileLocator | None = None,
    ) -> Path:
        """
        Store configuration for the given application by delegating to a format handler.

        Destination selection:
          - target="project": <project_root>/<project_search_path>/<filename>
          - target="user":    <user_base>/.config/<app_name>/<user_filename or filename>

        Handler delegation:
          - The handler is selected based on the destination file's suffix.
          - The selected handler performs the actual serialization and writes.

        Behavior:
          - Ensures the destination directory exists (created if necessary).
          - Overwrites existing files.
          - If no handler supports the destination suffix, a RuntimeError is raised.

        Args:
            cfg: Mapping of configuration values to persist.
            app_name: Application name; used for user config path resolution.
            project_search_path: Relative folder inside the project root for project-side configs
                (default: "config").
            filename: File name for the project-side config (default: "config.yaml").
            user_filename: Optional override for the user-side file name. If None, uses filename.
            target: Which destination to write: "project" or "user" (default: "user").
            file_util: Optional FileUtil instance. In production this is usually omitted
                (a new one will be created). In tests, you can supply a preconfigured
                FileUtil bound to a temporary project root or user base directory.

        Returns:
            Path: The full path to the file that was written.

        Raises:
            AssertionError: If app_name is empty or filename is not provided.
            RuntimeError: If no handler supports the destination suffix.
        """
        out_path, handler = self._resolve_output_and_handler(
            app_name=app_name,
            project_search_path=project_search_path,
            filename=filename,
            user_filename=user_filename,
            target=target,
            file_util=file_util,
        )
        handler.store(out_path, cfg)
        return out_path

    def update(
            self,
            patch: Mapping[str, Any],
            app_name: str,
            *,
            project_search_path: str | Path = "config",
            filename: str | Path = "config.yaml",
            user_filename: str | Path | None = None,
            target: Literal["project", "user"] = "user",
            file_util: ProjectFileLocator | None = None,
    ) -> Path:
        """
        Merge the given patch into the target config file and persist it.

        Behavior:
          - Resolves the destination similarly to store().
          - Loads existing config from the destination file only (does not combine sources).
          - Deep-merges existing config with the patch (the patch wins).
          - Writes the merged result back to the same destination.
        """
        out_path, handler = self._resolve_output_and_handler(
            app_name=app_name,
            project_search_path=project_search_path,
            filename=filename,
            user_filename=user_filename,
            target=target,
            file_util=file_util,
        )

        current_cfg: dict = handler.load(out_path) if out_path.exists() else {}
        merged = ConfigMerger.deep(current_cfg or {}, dict(patch))
        handler.store(out_path, merged)
        return out_path

    def _load_any(self, path: Path) -> dict:
        """
        Use the first loader that supports the file path.
        Only one loader is applied; loaders are not combined.
        Returns {} if no loader supports the path.
        """
        handler: ConfigFormatHandler = self._get_handler_for(path)
        return handler.load(path) if handler is not None else {}

    def _get_handler_for(self, path: Path) -> ConfigFormatHandler | None:
        """return the first loader that supports the file path, else done."""
        for h in self._handlers:
            if h.supports(path):
                return h
        return None

    def _resolve_output_and_handler(
            self,
            *,
            app_name: str,
            project_search_path: str | Path,
            filename: str | Path,
            user_filename: str | Path | None,
            target: Literal["project", "user"],
            file_util: ProjectFileLocator | None,
    ) -> tuple[Path, ConfigFormatHandler]:
        """
        Common resolution for store() and update():
        - validates inputs
        - computes out_path based on target
        - ensures that the parent directory exists
        - selects and returns the handler
        """
        g.ensure_not_empty_str(app_name, "app_name")
        g.ensure_usable_path(filename, "filename")

        fu = file_util or ProjectFileLocator()
        if target == "project":
            base = fu.get_project_root()
            out_path = base / Path(project_search_path or "") / Path(filename)
        else:
            f_name = Path(user_filename or filename)
            base = fu.get_user_base_dir()
            out_path = base / Path(".config") / app_name / f_name

        out_path.parent.mkdir(parents=True, exist_ok=True)

        handler = self._get_handler_for(out_path)
        if handler is None:
            raise RuntimeError(f"No handler available to store files with suffix '{out_path.suffix}'")

        return out_path, handler

    def store_to_path(self, cfg: Mapping[str, Any], path: Path) -> Path:
        """Serialize cfg to the given path using a handler chosen by suffix."""
        pass

    def update_path(self, patch: Mapping[str, Any], path: Path) -> Path:
        """Load existing cfg (if any), deep-merge patch, and store back."""
        pass
