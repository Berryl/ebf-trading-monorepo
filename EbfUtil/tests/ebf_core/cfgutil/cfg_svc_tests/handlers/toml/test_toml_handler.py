from pathlib import Path

import pytest

from ebf_core.cfgutil.handlers.toml_handler import TomlHandler


@pytest.fixture
def sut() -> TomlHandler:
    return TomlHandler()


class TestSupports:
    @pytest.mark.parametrize("filename", ["cfg.toml", "settings.TOML"])
    def test_supports_toml_suffix(self, sut, tmp_path: Path, filename: str):
        assert sut.supports(tmp_path / filename)

    @pytest.mark.parametrize("filename", ["cfg.yaml", "config.json", "data.toml.bak"])
    def test_does_not_support_other_suffixes(self, sut, tmp_path: Path, filename: str):
        assert not sut.supports(tmp_path / filename)


class TestLoad:
    def test_missing_file_returns_empty_dict(self, sut, tmp_path: Path):
        path = tmp_path / "missing.toml"
        assert not path.exists()

        result = sut.load(path)

        assert result == {}

    def test_can_load_valid_toml_into_dict(self, sut, tmp_path: Path):
        path = tmp_path / "cfg.toml"
        path.write_text(
            "[section]\n"
            "a = 1\n"
            "b = \"two\"\n",
            encoding="utf-8",
        )

        result = sut.load(path)

        assert result == {"section": {"a": 1, "b": "two"}}


class TestStore:
    def test_store_is_not_supported_and_always_raises(self, sut, tmp_path: Path):
        path = tmp_path / "cfg.toml"
        cfg = {"a": 1}

        with pytest.raises(RuntimeError, match="Writing TOML is not supported"):
            sut.store(path, cfg)
