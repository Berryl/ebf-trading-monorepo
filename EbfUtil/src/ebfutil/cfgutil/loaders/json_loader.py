import json
from pathlib import Path


class JsonLoader:
    file_types = (".json",)

    def supports(self, path: Path) -> bool: return path.suffix.lower() in self.file_types

    # noinspection PyMethodMayBeStatic
    def load(self, path: Path) -> dict:
        if not path.exists(): return {}
        return json.loads(path.read_text(encoding="utf-8")) or {}
