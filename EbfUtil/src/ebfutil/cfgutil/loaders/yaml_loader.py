from pathlib import Path

import yaml


class YamlLoader:
    suffixes = (".yaml", ".yml")

    def supports(self, path: Path) -> bool: return path.suffix.lower() in self.suffixes

    def load(self, path: Path) -> dict:
        if not path.exists(): return {}
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data or {}
