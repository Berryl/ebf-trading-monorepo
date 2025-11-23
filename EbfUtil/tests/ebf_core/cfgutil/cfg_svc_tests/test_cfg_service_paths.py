import json
from pathlib import Path
from typing import Callable

import pytest

from ebf_core.cfgutil.cfg_service import ConfigService


@pytest.fixture
def sut() -> ConfigService:
    return ConfigService()


@pytest.fixture
def write_json(tmp_path: Path) -> Callable:
    def _write(rel: str, data: dict) -> Path:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path
    return _write


class TestLoad:

    def test_when_single_source_file(self, sut, write_json):
        source = write_json("cfg.json", {"a": 1, "b": 2})

        cfg = sut.load(source)
        assert cfg == {"a": 1, "b": 2}

    def test_when_multiple_source_files(self, sut, write_json):
        project_file = write_json("project_file.json", {"a": 1, "nested": {"x": 1, "y": 2}})
        user_file = write_json("user_file.json", {"nested": {"y": 99, "z": 3}})

        cfg = sut.load(project_file, user_file)

        # Deep merge: user_file overrides, but existing keys are preserved
        assert cfg["a"] == 1
        assert cfg["nested"] == {"x": 1, "y": 99, "z": 3}  # key 'y' overridden by user_file

    def test_can_return_sources(self, sut, write_json, tmp_path):
        f1 = write_json("f1.json", {"a": 1})
        f2 = write_json("user_actual.json", {"b": 2})

        cfg, sources = sut.load(f1, f2, return_sources=True)

        assert sources == [f1, f2]

    def test_invalid_sources_are_ignored(self, sut, write_json, tmp_path):
        f1 = write_json("f1.json", {"a": 1})
        nonexistent_file = tmp_path / "f2.json"
        f2 = write_json("user_actual.json", {"b": 2})

        cfg, sources = sut.load(f1, nonexistent_file, f2, return_sources=True)

        # Only existing files, in the order they were applied
        assert nonexistent_file not in sources
        assert sources == [f1, f2]

    def test_when_no_paths_exist(self, sut, tmp_path):
        p1 = tmp_path / "missing1.json"
        p2 = tmp_path / "missing2.json"

        cfg = sut.load(p1, p2)
        assert cfg == {}
