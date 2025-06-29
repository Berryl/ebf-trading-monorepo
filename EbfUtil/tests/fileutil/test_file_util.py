import re
from unittest.mock import patch

import pytest

from fileutil.file_util import FileUtil, BASE_DIR_STRUCTURE


@pytest.mark.integration
class TestGetProjectRoot:
    @pytest.fixture
    def sut(self) -> FileUtil:
        return FileUtil()

    def test_get_project_root_returns_path_with_at_least_one_common_marker_when_no_args(self, sut):
        found = sut.get_project_root()
        assert any((found / m).exists() for m in sut.common_project_markers)

    def test_get_project_root_caches_when_no_args(self, sut):
        assert sut._cached_project_root is None
        found = sut.get_project_root()
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

    def test_get_project_root_raises_error_if_marker_list_is_empty_strings(self, sut):
        with pytest.raises(ValueError, match="Markers must be non-empty strings"):
            sut.get_project_root(markers=['', ''])

    def test_get_project_root_raises_error_if_priority_marker_is_invalid_strings(self, sut):
        msg = 'Priority marker must be a non-empty string'

        with pytest.raises(ValueError, match=msg):
            sut.get_project_root(priority_marker=42)

        with pytest.raises(ValueError, match=msg):
            sut.get_project_root(priority_marker="             ")


@pytest.mark.integration
class TestGetBaseDir:
    @pytest.fixture
    def sut(self) -> FileUtil:
        return FileUtil()

    def test_base_dir_is_investing(self):
        dir_name = str(BASE_DIR_STRUCTURE)
        assert dir_name.endswith('Investing'), f"Base folder name {dir_name} is not Investing"

    def test_get_base_dir_exists(self, sut):
        path = sut.get_base_dir()
        assert path.exists(), f"Base directory {path} does not exist"

    @pytest.mark.parametrize("filename", ['snapshot.xlsm', 'cagr.xlsm'])  # noqa
    def test_get_file_from_investing(self, sut, filename):
        path = sut.get_file_from_investing(filename)
        assert path.exists(), f"path {str(path)} does not exist"

    def test_get_file_from_investing_when_bad_filename_raises_error(self, sut):
        bad_filename = 'blah'
        bad_path = re.escape(str(sut.get_base_dir() / bad_filename))
        err_msg = fr"The file {bad_path} does not exist in the Investing directory."
        with pytest.raises(FileNotFoundError, match=err_msg):
            sut.get_file_from_investing(bad_filename)

    @pytest.mark.parametrize("username", ['smith'])
    def test_get_user_specific_path_adjust_for_any_user(self, sut, username):
        with patch('os.getlogin', return_value=username):  # noqa
            assert username in str(sut.get_user_specific_path())

    def test_get_testing_book_from_project_root(self, sut):
        file_path = sut.get_file_from_project_root('some_txt_file.txt', search_path=r'tests\fileutil')
        assert file_path.exists(), f"some_txt_file.txt does not exist at {file_path}"
