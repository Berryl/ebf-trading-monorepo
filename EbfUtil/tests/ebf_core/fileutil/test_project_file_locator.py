import logging
import os
import re
from pathlib import Path

import pytest

from ebf_core.fileutil.project_file_locator import ProjectFileLocator, logger


@pytest.fixture
def sut() -> ProjectFileLocator:
    return ProjectFileLocator()


@pytest.mark.integration
class TestWithProjectRoot:

    def test_project_root_default_is_none(self, sut):
        assert sut._project_root is None

    def test_use_cwd_default_is_false(self, sut):
        assert sut._use_cwd_as_root is False

    def test_with_project_root_creates_new_instance(self, sut, tmp_path):
        sut_clone = sut.with_project_root(tmp_path)
        assert sut_clone is not sut

    def test_with_project_root_when_arg_is_path(self, sut, tmp_path):
        assert sut._project_root != tmp_path

        assert sut.with_project_root(tmp_path)._project_root == tmp_path.resolve()

    def test_with_project_root_when_arg_is_none(self, sut, tmp_path):
        sut_with_path = sut.with_project_root(tmp_path)
        assert sut_with_path._project_root == tmp_path.resolve()

        sut_with_no_path = sut_with_path.with_project_root(None)
        assert sut_with_no_path._project_root is None

    def test_with_project_root_when_arg_is_none_and_use_cwd_is_true(self, sut, tmp_path):
        sut_with_cwd = sut.with_project_root(None, use_cwd_as_root=True)
        assert sut_with_cwd._project_root == Path.cwd().resolve()


@pytest.mark.integration
class TestWithMarkers:

    def test_marker_list_default_is_none(self, sut):
        assert sut._markers is None

    def test_priority_marker_default_is_none(self, sut):
        assert sut._priority_marker is None

    def test_with_markers_creates_new_instance(self, sut, tmp_path):
        sut_clone = sut.with_markers(['blah'])
        assert sut_clone is not sut

    def test_with_markers_is_immutable(self, sut):
        m = [".git"]
        s2 = sut.with_markers(m, priority=".git")
        assert sut._markers is None
        assert s2._markers == m and s2._priority_marker == ".git"


@pytest.mark.integration
class TestGetProjectRoot:

    def test_user_provided_project_root_is_returned_first_when_available(self, sut, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        sut.with_project_root(None, use_cwd_as_root=True).get_project_root()

        assert "user provided" in caplog.text

        assert "cached" not in caplog.text
        assert "marker search" not in caplog.text

    def test_markers_are_used_when_no_project_root_is_available(self, sut, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        sut.get_project_root()

        assert "user provided" not in caplog.text
        assert "cached" not in caplog.text

        assert "marker search" in caplog.text

    def test_default_markers_can_determine_the_project_root(self, sut, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        found = sut.get_project_root()
        assert found.exists()

        assert "Found marker '.git'" in caplog.text

    def test_the_start_path_is_returned_if_the_marker_search_fails(self, sut, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        found = sut.with_markers(["blah"]).get_project_root()
        assert found.exists() and found == sut._detect_start_path()

        assert "Found marker" not in caplog.text

    def test_markers_are_validated(self, sut):
        with pytest.raises(ValueError, match="Marker list must not be empty"):
            sut.with_markers([]).get_project_root()

    def test_cached_root_used_on_second_call(self, sut, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        sut.get_project_root()  # the first call has no cache and so performs the search
        assert "cached" not in caplog.text

        caplog.clear()
        sut.get_project_root()  # the second call should use cache
        assert "cached" in caplog.text


@pytest.mark.integration
class TestWithProjectFile:

    def test_relpath_default_is_none(self, sut):
        assert sut.project_file_relpath is None

    def test_cached_project_file_default_is_none(self, sut):
        assert sut._cached_project_file is None

    def test_a_new_instance_is_created(self, sut):
        sut_clone = sut.with_project_file()
        assert sut_clone is not sut

    def test_default_arg_is_known_default_path(self, sut):
        result = sut.with_project_file()
        assert result.project_file_relpath == Path(result.DEFAULT_PROJECT_FILE_RELATIVE_PATH)

    def test_arg_sets_the_relpath(self, sut):
        result = sut.with_project_file("pyproject.toml")
        assert result.project_file_relpath == Path("pyproject.toml")

    def test_none_arg_clears_the_relpath(self, sut):
        result = sut.with_project_file()
        assert result.project_file_relpath == Path(result.DEFAULT_PROJECT_FILE_RELATIVE_PATH)

        result = result.with_project_file(None)
        assert result.project_file_relpath is None

    def test_empty_str_args_are_trapped(self, sut):
        msg = re.escape("Arg 'relpath' cannot be an empty string")
        with pytest.raises(AssertionError, match=msg):
            sut.with_project_file("")

    def test_dot_path_is_not_allowed(self, sut):
        msg = re.escape("must be a *relative* path from the project root")
        msg =  f"'.' is not allowed.*{msg}"

        with pytest.raises(ValueError, match=msg):
            sut.with_project_file(".")

    def test_absolute_project_file_path_is_not_allowed(self, sut, tmp_path):
        assert tmp_path.is_absolute()

        msg = re.escape("must be a *relative* path from the project root")
        with pytest.raises(ValueError, match=msg):
            sut.with_project_file(tmp_path)

    @pytest.mark.skipif(os.name != "nt", reason="Windows-only quirk")
    def test_drive_anchored_relative_is_not_allowed(self, sut):
        msg = re.escape("must be a *relative* path from the project root")
        with pytest.raises(ValueError, match=msg):
            sut.with_project_file(Path("C:foo.txt"))


@pytest.mark.integration
class TestGetProjectFile:
    # helpers
    def _mk_proj(self, tmp_path: Path) -> tuple[ProjectFileLocator, Path]:
        root = tmp_path / "proj"
        (root / "cfg").mkdir(parents=True)
        loc = ProjectFileLocator().with_project_root(root)
        return loc, root

    @pytest.fixture
    def sut_with_root(self, tmp_path: Path) -> ProjectFileLocator:
        return ProjectFileLocator().with_project_root(root=None, use_cwd_as_root=True)

    def test_when_no_relpath_then_return_is_none(self, sut_with_root):
        assert sut_with_root.project_file_relpath is None

        assert sut_with_root.get_project_file() is None

    def test_when_default_file_is_used(self, sut_with_root):
        path = sut_with_root.with_project_file().get_project_file()
        assert path.exists() and path.name == "config.yaml"

    def test_when_nonexistent_relpath_is_used_default_is_error(self, sut_with_root):
        msg = re.escape("Project file not found: ")
        msg = f"^{msg}.*blah$"

        with pytest.raises(FileNotFoundError, match=msg):
            sut_with_root.with_project_file("blah").get_project_file()

    def test_when_nonexistent_relpath_is_used_without_requiring_existence(self, sut_with_root):
        path = sut_with_root.with_project_file("blah").get_project_file(must_exist=False)
        assert path.name == "blah", "this doesn't exist, but we told it not to require existence"

    def test_relative_path_arg_overrides_member_relative_path(self, sut_with_root):
        instance = sut_with_root.with_project_file()
        assert instance.project_file_relpath.name == 'config.yaml'

        path = instance.get_project_file("resources/settings.yaml", must_exist=True)
        assert path.name == "settings.yaml"

    def test_per_call_absolute_allowed_bypasses_restrict_to_root(self, tmp_path):
        loc, _ = self._mk_proj(tmp_path)
        outside = tmp_path / "outside.yaml"
        outside.write_text("x")
        p = loc.get_project_file(outside, must_exist=True, restrict_to_root=True)
        assert p == outside.resolve()

    def test_per_call_relative_escape_blocked_by_restrict_to_root(self, tmp_path):
        loc, root = self._mk_proj(tmp_path)
        (root / "cfg").mkdir(exist_ok=True)
        with pytest.raises(ValueError):
            loc.get_project_file("../outside.yaml", must_exist=False, restrict_to_root=True)

    def test_per_call_relative_escape_allowed_when_restrict_is_false(self, tmp_path):
        loc, root = self._mk_proj(tmp_path)
        outside = root.parent / "ok.yaml"
        outside.write_text("x")
        p = loc.get_project_file("../ok.yaml", must_exist=True, restrict_to_root=False)
        assert p == outside.resolve()

    def test_cached_used_only_for_sticky_default(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        loc, root = self._mk_proj(tmp_path)
        f = root / "cfg/app.yaml"
        f.write_text("ok")
        loc = loc.with_project_file("cfg/app.yaml")

        caplog.clear()
        loc.get_project_file(must_exist=True)  # prime cache
        caplog.clear()
        loc.get_project_file(must_exist=True)  # should hit cache
        assert "cached project file" in caplog.text.lower()

        caplog.clear()
        loc.get_project_file("cfg/app.yaml", must_exist=True)  # per-call: no cache
        assert "cached project file" not in caplog.text.lower()

    def test_use_cache_false_bypasses_cache(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        loc, root = self._mk_proj(tmp_path)
        f = root / "cfg/app.yaml"; f.write_text("ok")
        loc = loc.with_project_file("cfg/app.yaml")
        loc.get_project_file(must_exist=True)  # prime
        caplog.clear()
        loc.get_project_file(must_exist=True, use_cache=False)
        assert "cached project file" not in caplog.text.lower()

    def test_per_call_empty_string_is_rejected(self, sut):
        with pytest.raises(AssertionError, match="relpath"):
            sut.get_project_file("", must_exist=False)

    def test_per_call_dot_is_rejected(self, sut):
        with pytest.raises(ValueError):
            sut.get_project_file(Path("."), must_exist=False)

    def test_per_call_tilde_expands(self, tmp_path, monkeypatch):
        # Point HOME to tmp_path and create ~/cfg.yaml
        home = tmp_path / "home"; home.mkdir()
        monkeypatch.setenv("HOME", str(home))
        p = home / "cfg.yaml"; p.write_text("x")
        sut = ProjectFileLocator().with_project_root(None, use_cwd_as_root=True)
        got = sut.get_project_file("~/cfg.yaml", must_exist=True, restrict_to_root=False)
        assert got == p.resolve()

    def test_cache_is_cleared_when_sticky_changes(self, tmp_path, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        loc, root = self._mk_proj(tmp_path)
        f1 = root / "cfg/a.yaml"; f1.write_text("a")
        f2 = root / "cfg/b.yaml"; f2.write_text("b")

        loc = loc.with_project_file("cfg/a.yaml")
        loc.get_project_file(must_exist=True)
        loc = loc.with_project_file("cfg/b.yaml")  # new instance, cache cleared
        caplog.clear()
        loc.get_project_file(must_exist=True)
        assert "cached project file" not in caplog.text.lower()
