import json
from pathlib import Path

import pytest

from ebf_core.cfgutil.cfg_service import ConfigService


@pytest.fixture
def sut() -> ConfigService:
    return ConfigService()


@pytest.fixture
def write_json(tmp_path: Path):
    def _write(rel: str, data: dict) -> Path:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path
    return _write


class TestLoad:

    def test_returns_empty_dict_when_all_paths_missing(self, sut, tmp_path):
        p1 = tmp_path / "missing1.json"
        p2 = tmp_path / "missing2.json"

        cfg = sut.load(p1, p2)
        assert cfg == {}

    def test_loads_single_existing_file(self, sut, write_json):
        p = write_json("cfg.json", {"a": 1, "b": 2})

        cfg = sut.load(p)
        assert cfg == {"a": 1, "b": 2}

    def test_later_paths_override_earlier_ones(self, sut, write_json):
        project = write_json("project.json", {"a": 1, "nested": {"x": 1, "y": 2}})
        user = write_json("user.json", {"nested": {"y": 99, "z": 3}})

        cfg = sut.load(project, user)

        # Deep merge: user overrides, but existing keys are preserved
        assert cfg["a"] == 1
        assert cfg["nested"] == {"x": 1, "y": 99, "z": 3}

    def test_can_optionally_return_sources(self, sut, write_json, tmp_path):
        project = write_json("project.json", {"a": 1})
        user_missing = tmp_path / "user.json"  # not written
        user = write_json("user_actual.json", {"b": 2})

        cfg, sources = sut.load(project, user_missing, user, return_sources=True)

        assert cfg == {"a": 1, "b": 2}
        # Only existing files, in the order they were applied
        assert sources == [project, user]
