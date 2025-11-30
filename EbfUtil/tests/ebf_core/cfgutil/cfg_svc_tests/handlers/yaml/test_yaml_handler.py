from pathlib import Path

import pytest

from ebf_core.cfgutil.handlers.yaml_handler import YamlHandler


@pytest.fixture
def sut() -> YamlHandler:
    return YamlHandler()


class TestSupports:
    @pytest.mark.parametrize("filename", ["cfg.yaml", "settings.YAmL"])
    def test_supports_yaml_suffix(self, sut, tmp_path: Path, filename: str):
        assert sut.supports(tmp_path / filename)

    @pytest.mark.parametrize("filename", ["cfg.json", "settings.txt", "CFG", "data.yaml.bak"])
    def test_does_not_support_other_suffixes(self, sut, tmp_path: Path, filename: str):
        assert not sut.supports(tmp_path / filename)


class TestLoad:
    def test_missing_file_returns_empty_dict(self, sut, tmp_path: Path):
        path = tmp_path / "missing.yaml"
        assert not path.exists()

        result = sut.load(path)

        assert result == {}

    def test_can_load_valid_yaml_into_dict(self, sut, tmp_path: Path):
        path = tmp_path / "cfg.yaml"
        path.write_text("a: 1\nb: 2\nnested:\n  x: 10\n", encoding="utf-8")

        result = sut.load(path)

        assert result == {"a": 1, "b": 2, "nested": {"x": 10}}

    def test_yaml_comments_and_strings(self, sut, tmp_path: Path):
        path = tmp_path / "cfg.yaml"
        path.write_text(
            "a: 1  # comment\n"
            "b: \"x # not comment\"\n",
            encoding="utf-8"
        )

        result = sut.load(path)

        assert result == {"a": 1, "b": "x # not comment"}


class TestStore:

    def test_store(self, sut, tmp_path: Path):
        path = tmp_path / "nested" / "cfg.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)

        cfg = {"a": 1, "nested": {"x": 2}}

        sut.store(path, cfg)

        loaded = sut.load(path)
        assert loaded == cfg
