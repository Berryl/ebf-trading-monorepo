from pathlib import Path

import pytest

from ebf_core.fileutil.path_norm import norm_path


class TestNormPath:
    class TestValueArg:

        @pytest.mark.parametrize("value", ["icons/a.ico", Path("icons/a.ico")])
        def test_pathlike_input(self, value):
            p = norm_path(value, expand_user=False)
            assert p == Path("icons/a.ico")

        @pytest.mark.parametrize("value", [None, "", "     "])
        def test_none_or_empty_returns_none(self, value):
            assert norm_path(value) is None

    class TestBaseResolution:

        def test_relative_with_base_resolves_under_base(self, tmp_path):
            base = tmp_path / "cfg"
            base.mkdir()
            p = norm_path("icons/a.ico", base=base)
            assert p == (base / "icons" / "a.ico").resolve()

        def test_pathlike_with_base(self, tmp_path):
            base = tmp_path / "cfg"
            base.mkdir()
            input_path = Path("icons/a.ico")
            p = norm_path(input_path, base=base)
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

        def test_absolute_path_ignores_base(self, tmp_path):
            base = tmp_path / "base"
            absolute = tmp_path / "other" / "file.txt"
            p = norm_path(str(absolute), base=base)
            assert p == absolute

    class TestExpansion:

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

        def test_tilde_expands_to_home(self, tmp_path, monkeypatch):
            home = tmp_path / "home"
            home.mkdir()
            monkeypatch.setenv("HOME", str(home))
            monkeypatch.setenv("USERPROFILE", str(home))
            p = norm_path("~/x.txt")
            assert p == home / "x.txt"
            assert p.is_absolute()

        def test_tilde_disabled(self, tmp_path, monkeypatch):
            home = tmp_path / "home"
            home.mkdir()
            monkeypatch.setenv("HOME", str(home))
            monkeypatch.setenv("USERPROFILE", str(home))
            p = norm_path("~/x.txt", expand_user=False)
            assert str(p) == "~/x.txt"
            assert not p.is_absolute()

        def test_env_var_with_tilde(self, tmp_path, monkeypatch):
            """Env vars should expand before tilde expansion."""
            home = tmp_path / "home"
            home.mkdir()
            monkeypatch.setenv("HOME", str(home))
            monkeypatch.setenv("USERPROFILE", str(home))
            monkeypatch.setenv("SUBDIR", "docs")

            p = norm_path("~/$SUBDIR/file.txt")
            assert p == home / "docs" / "file.txt"
