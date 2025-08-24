from pathlib import Path

try:
    import tomllib  # py3.11+
except Exception:  # pragma: no cover
    tomllib = None


class TomlLoader:
    file_types = (".toml",)

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.file_types

    def load(self, path: Path) -> dict:
        if not path.exists(): return {}
        if tomllib is None:
            raise RuntimeError("TOML support requires Python 3.11+ (tomllib).")
        return tomllib.loads(path.read_text(encoding="utf-8")) or {}
