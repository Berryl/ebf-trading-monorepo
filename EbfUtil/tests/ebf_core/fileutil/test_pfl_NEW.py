import logging
from pathlib import Path

import pytest

from ebf_core.fileutil.pfl_NEW import ProjectFileLocator, logger

logger.addHandler(logging.FileHandler('test.log', mode='w'))
logger.setLevel(logging.DEBUG)

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
        assert sut_with_cwd._project_root == Path.cwd()



@pytest.mark.integration
class TestWithMarkers:

    def test_marker_list_default_is_none(self, sut):
        assert sut._markers is None

    def test_priority_marker_default_is_none(self, sut):
        assert sut._priority_marker is None

    def test_with_markers_creates_new_instance(self, sut, tmp_path):
        sut_clone = sut.with_markers(['blah'])
        assert sut_clone is not sut


@pytest.mark.integration
class TestGetProjectRoot:

    def test_user_provided_project_root_is_returned_first_when_available(self, sut, caplog):
        sut.with_project_root(None, use_cwd_as_root=True).get_project_root()

        assert "user provided" in caplog.text

        assert "cached" not in caplog.text
        assert "marker search" not in caplog.text

    def test_markers_are_used_when_no_project_root_is_available(self, sut, caplog):
        sut.get_project_root()

        assert "user provided" not in caplog.text
        assert "cached" not in caplog.text

        assert "marker search" in caplog.text

    def test_default_markers_can_determine_the_project_root(self, sut, caplog):
        found = sut.get_project_root()
        assert found.exists()

        assert "Found marker '.git'" in caplog.text

    def test_the_start_path_is_returned_if_the_marker_search_fails(self, sut, caplog):
        found = sut.with_markers(["blah"]).get_project_root()
        assert found.exists()

        assert "Found marker" not in caplog.text

    def test_markers_are_validated(self, sut):
        with pytest.raises(ValueError, match="Marker list must not be empty"):
            sut.with_markers([]).get_project_root()
