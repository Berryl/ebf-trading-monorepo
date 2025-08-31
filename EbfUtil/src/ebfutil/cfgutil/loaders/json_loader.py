import json
from pathlib import Path
from typing import Mapping


class JsonLoader:
    file_types = (".json",)

    def supports(self, path: Path) -> bool: return path.suffix.lower() in self.file_types

    # noinspection PyMethodMayBeStatic
    def load(self, path: Path) -> dict:
        if not path.exists(): return {}
        return json.loads(path.read_text(encoding="utf-8")) or {}

    # noinspection PyMethodMayBeStatic
    def store(self, path: Path, cfg: Mapping[str, Any]) -> None:
        """
        Serialize cfg as pretty-printed JSON and write to path. Overwrites existing files.
        """
        text = json.dumps(cfg, indent=2, ensure_ascii=False)
        path.write_text(text, encoding="utf-8")
