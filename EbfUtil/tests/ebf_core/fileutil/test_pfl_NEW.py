from pathlib import Path

import pytest

from ebf_core.fileutil.pfl_NEW import ProjectFileLocator


@pytest.fixture
def sut() -> ProjectFileLocator:
    return ProjectFileLocator()


@pytest.mark.integration
class TestProjectRootMember:

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
