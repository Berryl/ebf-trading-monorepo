import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class YamlLoader:
    file_types = (".yaml", ".yml")
    default_file_extension = "yaml"

    def supports(self, path: Path) -> bool: return path.suffix.lower() in self.file_types

    # noinspection PyMethodMayBeStatic
    def load(self, path: Path) -> dict:
        try:
            with open(path, 'r', encoding='utf-8') as file:
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