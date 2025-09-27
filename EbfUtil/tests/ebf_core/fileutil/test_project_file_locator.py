from unittest.mock import patch

import pytest

from ebf_core.fileutil.project_file_locator import ProjectFileLocator

VALID_SEARCH_PATH = r'tests/ebf_core/fileutil'  # noqa


@pytest.mark.integration
class TestProjectRootOverride:
    """
    Tests for FileUtil project_root_override behavior.

    Ensures FileUtil can work both in its own repo
    (by marker search) and with an explicit override
    provided by consuming projects.

    The pytest supplied fixture "tmp_path" provides a unique, empty temp directory.
    This simulates an external consuming project defining its root explicitly.
    """

    def test_can_find_file_inside_ebf_util_without_override(self):
        sut = ProjectFileLocator()
        file_path = sut.get_file_from_project_root('some_txt_file.txt', search_path=VALID_SEARCH_PATH)
        assert sut._project_root_override is None
        assert file_path.exists(), f"some_txt_file.txt does not exist at {file_path}"

    def test_can_find_file_inside_external_project_with_override_in_init(self, tmp_path):
        sut = ProjectFileLocator(project_root_override=tmp_path)
        result = sut.get_project_root()
        assert result == tmp_path

    def test_can_find_file_inside_external_project_with_override_in_setter(self, tmp_path):
        sut = ProjectFileLocator()
        sut.set_project_root_override(tmp_path)
        result = sut.get_project_root()
        assert result == tmp_path


@pytest.mark.integration
class TestGetProjectRoot:
    @pytest.fixture
    def sut(self) -> ProjectFileLocator:
        return ProjectFileLocator()

    def test_get_project_root_returns_path_with_at_least_one_common_marker_when_no_args(self, sut):
        found = sut.get_project_root()
        assert any((found / m).exists() for m in sut.common_project_markers)

    def test_get_project_root_caches_when_no_args(self, sut):
        assert sut._cached_project_root is None
        found = sut.get_project_root()
        print(found)
        assert sut._cached_project_root is not None, f"{found} was not cached"

    def test_get_project_root_will_not_cache_when_specified(self, sut):
        assert sut._cached_project_root is None
        sut.get_project_root(use_cache=False)
        assert sut._cached_project_root is None

    def test_get_project_root_uses_marker_list_if_specified(self, sut):
        found = sut.get_project_root(markers=['.idea'])

        assert sut._cached_project_root == found, f"{found} was not cached"
        assert (found / '.idea').exists()

    def test_get_project_root_uses_priority_marker_if_specified(self, sut):
        found = sut.get_project_root(priority_marker='.idea')

        assert sut._cached_project_root == found, f"{found} was not cached"
        assert (found / '.idea').exists()

    def test_get_file_from_project_root_with_search_path(self, sut):
        file_path = sut.get_file_from_project_root('some_txt_file.txt', search_path=VALID_SEARCH_PATH)
        assert file_path.exists(), f"some_txt_file.txt does not exist at {file_path}"

    def test_get_file_from_project_root_when_bad_filename_raises_error(self, sut):
        err_msg = "The 'project root' file 'blah' does not exist in the '' folder. "
        with pytest.raises(FileNotFoundError, match=err_msg):
            sut.get_file_from_project_root('blah')

    def test_get_project_root_raises_error_if_marker_list_is_empty_strings(self, sut):
        with pytest.raises(ValueError, match="Markers must be non-empty strings"):
            sut.get_project_root(markers=['', ''])

    def test_get_project_root_raises_error_if_priority_marker_is_invalid_strings(self, sut):
        msg = 'Priority marker must be a non-empty string'

        with pytest.raises(ValueError, match=msg):
            sut.get_project_root(priority_marker=42)

        with pytest.raises(ValueError, match=msg):
            sut.get_project_root(priority_marker="             ")

    def test_try_get_project_file_with_search_path_found(self, sut):
        p = sut.try_get_file_from_project_root("some_txt_file.txt",search_path=VALID_SEARCH_PATH,)
        assert p is not None and p.exists()

    def test_try_get_project_file_missing_returns_none(self, sut):
        p = sut.try_get_file_from_project_root("does_not_exist.txt")
        assert p is None


@pytest.mark.integration
class TestUserBaseStructure:
    @pytest.fixture
    def sut(self) -> ProjectFileLocator:
        return ProjectFileLocator()

    def test_default_base_dir(self, sut):
        path = str(sut.base_structure)
        assert path.endswith('Investing')

    def test_get_base_dir_when_using_default_base_structure(self, sut):
        path = sut.get_user_base_dir()
        assert str(path).endswith('Investing')

    @pytest.mark.parametrize("filename", ['snapshot.xlsm', 'cagr.xlsm'])  # noqa
    def test_get_file_from_user_base(self, sut, filename):
        path = str(sut.get_file_from_user_base_dir(filename))
        assert path.endswith(filename)

    def test_get_file_from_user_base_with_search_path(self, sut):
        path = sut.get_file_from_user_base_dir('constants.xlsm', search_path='dev')
        assert path.exists()

    def test_get_file_from_user_base_when_bad_filename_raises_error(self, sut):
        err_msg = "The 'user' file 'blah' does not exist in the 'Investing' folder. "
        with pytest.raises(FileNotFoundError, match=err_msg):
            sut.get_file_from_user_base_dir('blah')

    @pytest.mark.parametrize("username", ['smith', 'jones'])
    def test_get_user_base_dir_adjusts_for_any_user(self, sut, username):
        with patch('os.getlogin', return_value=username):  # noqa
            assert username in str(sut.get_user_base_dir())

    def test_try_get_file_from_user_base_dir_with_search_path_found(self, sut):
        p = sut.try_get_file_from_user_base_dir('constants.xlsm', search_path='dev')
        assert p is not None and p.exists()

    def test_try_get_file_from_user_base_dir_not_found_returns_none(self, sut):
        p = sut.try_get_file_from_user_base_dir("does_not_exist.txt")
        assert p is None
