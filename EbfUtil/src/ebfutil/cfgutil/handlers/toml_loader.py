from pathlib import Path
from typing import Any, Mapping

from ebfutil.cfgutil.handlers.cfg_format_handler import ConfigFormatHandler

try:
    import tomllib  # py3.11+
except ImportError:  # pragma: no cover
    tomllib = None


class TomlLoader(ConfigFormatHandler):
    """
    A loader for TOML configuration files.

    Supports reading TOML files using Python's standard library 'tomllib' (3.11+).
    Writing is not supported.
    """
    file_types = (".toml",)

    def load(self, path: Path) -> dict:
        if not path.exists(): return {}
        if tomllib is None:
            raise RuntimeError("TOML support requires Python 3.11+ (tomllib).")
        return tomllib.loads(path.read_text(encoding="utf-8")) or {}

    def store(self, path: Path, cfg: Mapping[str, Any]) -> None:
        """
        Writing is not available with toml.
        """
        raise RuntimeError("Writing TOML is not supported by this service.")
