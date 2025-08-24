import json
from pathlib import Path


class JsonLoader:
    suffixes = (".json",)

    def supports(self, path: Path) -> bool: return path.suffix.lower() in self.suffixes

    def load(self, path: Path) -> dict:
        if not path.exists(): return {}
        return json.loads(path.read_text(encoding="utf-8")) or {}
