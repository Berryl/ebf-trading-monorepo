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
    #
    # def test_with_project_root_when_arg_is_none(self, sut, tmp_path):
    #     sut = ProjectFileLocator(project_root=tmp_path)
    #     assert sut._project_root == tmp_path.resolve()
    #
    #     sut.with_project_root(None)
    #     assert sut._project_root is None
    #
    # def test_with_project_root_when_arg_is_none_and_use_cwd_is_true_from_init(self, sut, tmp_path):
    #     sut = ProjectFileLocator(project_root=tmp_path, use_cwd_as_root=True)
    #
    #     sut.with_project_root(None)
    #     assert sut._project_root == Path.cwd(), "project_root should be Path.cwd()"
    #
    # def test_with_project_root_when_arg_is_none_and_use_cwd_is_true_from_arg(self, sut, tmp_path):
    #     sut = ProjectFileLocator(project_root=tmp_path)
    #     assert sut._use_cwd_as_root is False
    #
    #     sut.with_project_root(None, use_cwd_as_root=True)
    #     assert sut._project_root == Path.cwd(), "project_root should be Path.cwd()"
    #
    # def test_when_project_root_path_is_set(self, sut, tmp_path):
    #     expected_root = tmp_path
    #     sut = ProjectFileLocator(project_root=expected_root)
    #     assert sut._project_root == expected_root
    #     assert sut.get_project_root() == expected_root, "project_root s/b project_root arg"
    # 
    # def test_when_project_root_is_none_and_use_cwd_flag_is_true(self):
    #     sut = ProjectFileLocator(use_cwd_as_root=True)
    #     expected_root = Path.cwd().resolve()
    #     assert sut._project_root == expected_root
    #     assert sut.get_project_root() == expected_root, "project_root s/b Path.cwd().resolve()"
    # 
    # def test_project_root_arg_has_precedence_when_use_cwd_flag_is_true(self, tmp_path):
    #     sut = ProjectFileLocator(use_cwd_as_root=True, project_root=tmp_path)
    #     expected_root = tmp_path
    #     assert sut._project_root == expected_root
    #     assert sut.get_project_root() == expected_root, "project_root s/b the project_root arg"
