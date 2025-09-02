import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ebf_core.cfgutil.handlers.cfg_format_handler import ConfigFormatHandler


class JsonHandler(ConfigFormatHandler):
    """
    A handler for JSON configuration files.
    """
    file_types = (".json",)

    def load(self, path: Path) -> dict:
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8")) or {}

    def store(self, path: Path, cfg: Mapping[str, Any]) -> None:
        """
        Serialize cfg as pretty-printed JSON and write to the path.
        Overwrites existing files.
        """
        text = json.dumps(cfg, indent=2, ensure_ascii=False)
        path.write_text(text, encoding="utf-8")
