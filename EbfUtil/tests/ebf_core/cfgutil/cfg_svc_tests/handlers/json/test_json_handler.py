from pathlib import Path

import pytest

from ebf_core.cfgutil.handlers.json_handler import JsonHandler


@pytest.fixture
def sut() -> JsonHandler:
    return JsonHandler()


class TestSupports:
    @pytest.mark.parametrize("filename", ["cfg.json", "settings.JSON"])
    def test_supports_json_suffix(self, sut, tmp_path: Path, filename: str):
        assert sut.supports(tmp_path / filename)

    @pytest.mark.parametrize("filename", ["cfg.yaml", "settings.txt", "CFG", "data.json.bak"])
    def test_does_not_support_other_suffixes(self, sut, tmp_path: Path, filename: str):
        assert not sut.supports(tmp_path / filename)


class TestLoad:
    def test_missing_file_returns_empty_dict(self, sut, tmp_path: Path):
        path = tmp_path / "missing.json"
        assert not path.exists()

        result = sut.load(path)

        assert result == {}

    def test_can_load_valid_json_into_dict(self, sut, tmp_path: Path):
        path = tmp_path / "cfg.json"
        path.write_text('{"a": 1, "b": 2}', encoding="utf-8")

        result = sut.load(path)

        assert result == {"a": 1, "b": 2}


class TestStore:
    def test_store_writes_json_that_round_trips_via_load(self, sut, tmp_path: Path):
        path = tmp_path / "nested" / "cfg.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        cfg = {"a": 1, "nested": {"x": 2}}

        sut.store(path, cfg)

        loaded = sut.load(path)
        assert loaded == cfg
