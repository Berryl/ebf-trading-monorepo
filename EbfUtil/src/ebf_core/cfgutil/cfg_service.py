from collections.abc import Mapping
from pathlib import Path
from typing import Any, Optional

from ebf_core.guards import guards as g
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

    def store(self, cfg: Mapping[str, Any], path: Path) -> Path:
        """
        Store configuration to the given path using a format handler.

        Why:
            Callers decide *where* configs live (project/user/other).
            ConfigService only needs to choose the right handler and
            perform the serialization.
        """
        g.ensure_type(path, Path, "path")

        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        handler = self._get_handler_for(path)
        if handler is None:
            raise RuntimeError(f"No handler available to store files with suffix '{path.suffix}'")

        handler.store(path, cfg)
        return path

    def update(self, patch: Mapping[str, Any], path: Path) -> Path:
        """
        Merge the patch into the config at the given path and persist it.

        Why:
            Callers choose a single concrete destination; this method
            lets them update that layer in place using deep-merge semantics.
        """
        g.ensure_type(path, Path, "path")

        path = path.resolve()
        path.parent.mkdir(parents=True, exist_ok=True)

        handler = self._get_handler_for(path)
        if handler is None:
            raise RuntimeError(f"No handler available to store files with suffix '{path.suffix}'")

        current: dict = handler.load(path) if path.exists() else {}
        merged = ConfigMerger.deep(current or {}, dict(patch))

        handler.store(path, merged)
        return path

    def _get_handler_for(self, path: Path) -> ConfigFormatHandler | None:
        """return the first loader that supports the file path, else done."""
        for h in self._handlers:
            if h.supports(path):
                return h
        return None
