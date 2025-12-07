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

    def test_relative_without_base_keeps_relative(self, tmp_path, monkeypatch):
        """Relative paths without a base should remain relative (not resolved to cwd)."""
        monkeypatch.chdir(tmp_path)

        p = norm_path("icons/a.ico")

        # The key assertions
        assert not p.is_absolute()
        assert p == Path("icons/a.ico")

        # Verify it didn't resolve against cwd
        assert p != (tmp_path / "icons" / "a.ico")
        assert p != (tmp_path / "icons" / "a.ico").resolve()

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

    def test_env_var_expands(self, tmp_path, monkeypatch):
        test_dir = tmp_path / "test"
        test_dir.mkdir()
        monkeypatch.setenv("TEST_DIR", str(test_dir))
        p = norm_path("$TEST_DIR/file.txt")
        assert p == test_dir / "file.txt"

    def test_env_var_disabled(self, monkeypatch):
        monkeypatch.setenv("TEST_DIR", "/some/path")
        p = norm_path("$TEST_DIR/file.txt", expand_env=False)
        assert "$TEST_DIR" in str(p)

    def test_absolute_path_ignores_base(self, tmp_path):
        base = tmp_path / "base"
        absolute = tmp_path / "other" / "file.txt"
        p = norm_path(str(absolute), base=base)
        assert p == absolute
