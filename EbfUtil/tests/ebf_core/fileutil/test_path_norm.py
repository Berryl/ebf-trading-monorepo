from pathlib import Path

import pytest

from ebf_core.fileutil.path_norm import norm_path

class TestNormPath:
    def test_none_returns_none(self, tmp_path):
        assert norm_path(None) is None

    @pytest.mark.parametrize("value", ["", "     "])
    def test_empty_str_returns_none(self, value):
        assert norm_path(value) is None

    def test_relative_with_base_resolves_under_base(self, tmp_path):
        base = tmp_path / "cfg"
        base.mkdir()
        p = norm_path("icons/a.ico", base=base)
        assert p == (base / "icons" / "a.ico").resolve()

    def test_relative_without_base_keeps_relative_when_not_required_absolute(self):
        p = norm_path("icons/a.ico")
        assert p == Path("icons/a.ico")
        assert not p.is_absolute()

    def test_relative_without_base_raises_when_require_absolute_true(self):
        with pytest.raises(ValueError):
            norm_path("icons/a.ico", require_absolute=True)

    def test_tilde_expands_to_home(self, tmp_path, monkeypatch):
        home = tmp_path / "home"
        home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        monkeypatch.setenv("USERPROFILE", str(home))
        p = norm_path("~/x.txt")
        assert p == home / "x.txt"
        assert p.is_absolute()
