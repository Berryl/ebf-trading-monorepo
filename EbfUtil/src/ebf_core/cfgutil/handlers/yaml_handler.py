import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from ebf_core.cfgutil.handlers.cfg_format_handler import ConfigFormatHandler

logger = logging.getLogger(__name__)


class YamlHandler(ConfigFormatHandler):
    """
    A handler for YAML configuration files.
    """
    file_types = (".yaml", ".yml")

    def load(self, path: Path) -> dict:
        try:
            with open(path, encoding='utf-8') as file:
                data = yaml.safe_load(file)
                return data or {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {path}: {e}")
            return {}
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding file {path}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error loading file {path}: {e}")
            return {}

    def store(self, path: Path, cfg: Mapping[str, Any]) -> None:
        """
        Serialize cfg as YAML and write to the path.
        Overwrites existing files.
        """
        text = yaml.safe_dump(dict(cfg), sort_keys=False)
        path.write_text(text, encoding="utf-8")
