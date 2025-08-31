from pathlib import Path
from typing import Any, Mapping

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    tomllib = None


class TomlLoader:
    file_types = (".toml",)

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.file_types

    # noinspection PyMethodMayBeStatic
    def load(self, path: Path) -> dict:
        if not path.exists(): return {}
        if tomllib is None:
            raise RuntimeError("TOML support requires Python 3.11+ (tomllib).")
        return tomllib.loads(path.read_text(encoding="utf-8")) or {}

    # noinspection PyMethodMayBeStatic
    def store(self, path: Path, cfg: Mapping[str, Any]) -> None:
        """
        Writing is not available with toml.
        """
        raise RuntimeError("Writing TOML is not supported by this service.")
