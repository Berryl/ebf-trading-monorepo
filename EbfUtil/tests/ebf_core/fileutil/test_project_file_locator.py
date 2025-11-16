import logging
import os
import re
from pathlib import Path

import pytest
from contextlib import nullcontext as does_not_raise
from ebf_core.fileutil.project_file_locator import ProjectFileLocator, logger


@pytest.fixture
def sut() -> ProjectFileLocator:
    return ProjectFileLocator()


@pytest.mark.integration
class TestWithProjectRoot:

    def test_project_root_default_is_none(self, sut):
        assert sut._project_root is None

    def test_new_instance_is_created(self, sut, tmp_path):
        sut_clone = sut.with_project_root(tmp_path)
        assert sut_clone is not sut

    def test_when_arg_is_path(self, sut, tmp_path):
        assert sut.project_root != tmp_path

        expected = tmp_path.resolve()
        actual = sut.with_project_root(tmp_path).project_root
        assert actual == expected

    def test_arg_of_none_resets_the_root_to_none(self, sut, tmp_path):
        sut_with_path = sut.with_project_root(tmp_path)
        assert sut_with_path.project_root == tmp_path.resolve()

        sut_with_no_path = sut_with_path.with_project_root(None)
        assert sut_with_no_path.project_root is None


@pytest.mark.integration
class TestWithCwdProjectRoot:

    def test_new_instance_is_created(self, sut):
        sut_clone = sut.with_cwd_project_root()
        assert sut_clone is not sut

    def test_project_root_is_cwd(self, sut):
        expected = Path.cwd().resolve()
        actual = ProjectFileLocator().with_cwd_project_root().project_root
        assert actual == expected


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

    def test_user_provided_project_root_is_returned_first_when_available(self, rooted_sut, caplog):
        caplog.set_level(logging.DEBUG, logger=logger.name)
        rooted_sut.get_project_root()

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

    def test_empty_str_is_error(self, sut):
        msg = re.escape("Arg 'relpath' cannot be an empty string")

        with pytest.raises(AssertionError, match=msg):
            sut.with_project_file("")

    def test_single_dot_is_not_allowed(self, sut):
        msg = re.escape("'.' is not allowed as a project file")

        with pytest.raises(ValueError, match=msg):
            sut.with_project_file(".")

    def test_tilde_expanded_is_not_allowed(self, rooted_sut):
        msg = "~ expansion is not allowed in with_project_file."

        with pytest.raises(ValueError, match=msg):
            rooted_sut.with_project_file("~/settings.yaml")

    def test_none_arg_clears_the_relpath(self, sut):
        result = sut.with_project_file()
        assert result.project_file_relpath == Path(result.DEFAULT_PROJECT_FILE_RELATIVE_PATH)

        result = result.with_project_file(None)
        assert result.project_file_relpath is None

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


@pytest.fixture
def rooted_sut() -> ProjectFileLocator:
    return ProjectFileLocator().with_cwd_project_root()

@pytest.mark.integration
class TestGetProjectFileRelpath:

    def test_when_relpath_never_set(self, rooted_sut):
        assert rooted_sut.project_file_relpath is None

        path = rooted_sut.get_project_file()
        assert path is None

    def test_whn_default_file_set_by_fluent_builder(self, rooted_sut):
        pfl = rooted_sut.with_project_file() # this uses the default file

        path = pfl.get_project_file()
        assert path.exists() and path.name == "config.yaml"

    def test_can_catch_nonexistent_path(self, rooted_sut):
        nonexistent_filename = "blah"
        msg = f"^{re.escape('Project file not found: ')}.*{nonexistent_filename}$"

        with (pytest.raises(FileNotFoundError, match=msg)):
            rooted_sut.with_project_file("blah").get_project_file()

    def test_can_override_existence_check(self, rooted_sut):
        path = (rooted_sut.with_project_file("blah")
                .get_project_file(must_exist=False))
        assert not path.exists() and path.name == "blah"

    def test_can_supply_relpath_per_call(self, rooted_sut):
        pfl = rooted_sut.with_project_file()
        assert pfl.project_file_relpath.name == 'config.yaml'

        path = pfl.get_project_file("resources/settings.yaml", must_exist=True)
        assert pfl.project_file_relpath.name == 'config.yaml', "relpath member should not change"
        assert path.name == "settings.yaml", "relpath uses supplied arg on this call"

    def test_relpath_can_be_absolute(self, rooted_sut):
        some_absolute_path = Path("C:/Windows/System32/notepad.exe").resolve()
        pfl = rooted_sut.with_project_file()

        path = pfl.get_project_file(some_absolute_path)
        assert path == some_absolute_path

    def test_nonexistent_absolute_path_must_exist_by_default(self, rooted_sut):
        nonexistent_path = Path("C:/this_file_does_not_exist_12345")
        msg = f"^{re.escape('Project file not found: ')}.*{re.escape(str(nonexistent_path))}"

        with (pytest.raises(FileNotFoundError, match=msg)):
            rooted_sut.with_project_file().get_project_file(nonexistent_path)

        with does_not_raise():  # allow non-existent with param must_exist=False
            rooted_sut.with_project_file().get_project_file(nonexistent_path, must_exist=False)


@pytest.mark.integration
class TestGetProjectFileRelpathRootRestriction:

    @pytest.fixture
    def outside_relpath(self) -> Path:
        return Path('..') / Path(__file__).name

    def test_default_restricts_relpath_escape_from_root(self, rooted_sut, outside_relpath):
        # restrict_to_root=True by default
        with pytest.raises(ValueError, match="Resolved path escapes project root"):
            rooted_sut.get_project_file(relpath=outside_relpath)

    def test_can_allow_relpath_escape_from_root(self, rooted_sut, outside_relpath):
        with does_not_raise():
            rooted_sut.get_project_file(relpath=outside_relpath, restrict_to_root=False, must_exist=False)


@pytest.mark.integration
class TestGetProjectFileCaching:
    @pytest.fixture
    def caplog(self, caplog):
        caplog.set_level(logging.DEBUG, logger="ebf_core.fileutil.project_file_locator")
        caplog.clear()
        yield caplog
        caplog.clear()

    @pytest.fixture
    def path1(self) -> Path:
        return Path("resources/config.yaml")

    @pytest.fixture
    def path2(self) -> Path:
        return Path("resources/settings.yaml")

    def test_cached_is_used_on_second_call_by_default(self, rooted_sut, caplog, path1):
        instance = rooted_sut.with_project_file(path1)

        instance.get_project_file()  # 1st call to prime cache
        caplog.clear()

        instance.get_project_file()  # 2nd call uses cache
        assert "cached project file" in caplog.text.lower()

    def test_cache_can_be_bypassed(self, rooted_sut, caplog, path1):
        instance = rooted_sut.with_project_file(path1)

        instance.get_project_file()  # prime cache
        caplog.clear()

        instance.get_project_file(use_cache=False)  # explicit cache bypass
        assert "cached project file" not in caplog.text.lower()
        assert "Using previously set sticky project file"

    def test_cache_is_cleared_when_per_call_relpath_changes(self, rooted_sut, caplog, path1, path2):
        instance = rooted_sut.with_project_file(path1)

        instance.get_project_file()  # prime cache
        caplog.clear()

        instance.get_project_file(path2)  # 2nd call uses a new path so no cache
        assert "cached project file" not in caplog.text.lower()
        assert "Using previously set sticky project file"


@pytest.mark.integration
class TestGetProjectFilePathExpansion:

    def test_tilde_expansion_works_when_no_exitance_check(self, rooted_sut):
        path = rooted_sut.get_project_file("~/settings.yaml", must_exist=False)
        assert path.name == "settings.yaml"

    def test_tilde_expansion_fails_with_exitance_check(self, rooted_sut):
        msg = "Cannot use ~ expansion and existence check: '~/settings.yaml'"

        with pytest.raises(ValueError, match=msg):
            rooted_sut.get_project_file("~/settings.yaml", must_exist=True)
