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
            assert p.as_posix() == "~/x.txt"
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

        def test_tilde_expands_to_custom_home(self, tmp_path):
            """Tilde should expand to the custom home when provided."""
            custom_home = tmp_path / "custom-home"
            custom_home.mkdir()

            p = norm_path("~/config.yml", home=custom_home)

            assert p == custom_home / "config.yml"
            assert p.is_absolute()

        def test_tilde_with_subdir_expands_to_custom_home(self, tmp_path):
            """Tilde with a nested path should expand to the custom home."""
            custom_home = tmp_path / "custom-home"
            custom_home.mkdir()

            p = norm_path("~/.config/app/settings.yml", home=custom_home)

            assert p == custom_home / ".config" / "app" / "settings.yml"
            assert p.parent.parent == custom_home / ".config"

        def test_custom_home_ignored_when_expand_user_false(self, tmp_path):
            """Custom home should be ignored if expand_user=False."""
            custom_home = tmp_path / "custom-home"
            custom_home.mkdir()

            p = norm_path("~/config.yml", home=custom_home, expand_user=False)

            assert p == Path("~/config.yml")
            assert not p.is_absolute()

        def test_tilde_user_falls_back_to_standard_expansion(self, tmp_path):
            """~username should fall back to system expansion (can't override other users)."""
            custom_home = tmp_path / "custom-home"
            custom_home.mkdir()

            # ~other-user should use standard Path.expanduser(), not custom home
            p = norm_path("~root/file.txt", home=custom_home)

            # This will expand to the real root user's home (or fail)
            # We can't easily control ~other-user expansion
            assert p != custom_home / "root" / "file.txt"

        def test_custom_home_with_base_resolution(self, tmp_path):
            """Custom home expansion should work before base resolution."""
            custom_home = tmp_path / "custom-home"
            custom_home.mkdir()
            base = tmp_path / "project"
            base.mkdir()

            # ~ expands first, then if still relative, the base applies.
            # But ~ always makes it absolute, so base won't apply
            p = norm_path("~/config.yml", home=custom_home, base=base)

            assert p == custom_home / "config.yml"
            # base is ignored because ~ made it absolute
