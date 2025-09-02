from abc import ABC, abstractmethod
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class ConfigFormatHandler(ABC):
    """
    Abstract base class that all config format handlers must follow.

    Each handler manages a specific file type (YAML, JSON, TOML, etc.)
    and advertises which filename suffixes it supports.
    """
    file_types: tuple[str, ...]  # The filename suffixes this handler supports.

    def supports(self, path: Path) -> bool:
        """Check if this handler can handle a given path's suffix file type."""
        return path.suffix.lower() in self.file_types

    @abstractmethod
    def load(self, path: Path) -> dict:
        """
        Load and parse the file into a dict. The dict will be empty if an error
        is encountered or the file has no data. Caller is responsible for ensuring
        the file exists.

        Implementations should handle errors gracefully and return an empty dict.
        """
        pass

    @abstractmethod
    def store(self, path: Path, cfg: Mapping[str, Any]) -> None:
        """
        Serialize and write cfg to the given path using this handler's format.
        Implementations should overwrite existing files and create parent
        directories if needed (or expect caller to do so as agreed).

        Implementations should handle errors gracefully.
        """
        pass