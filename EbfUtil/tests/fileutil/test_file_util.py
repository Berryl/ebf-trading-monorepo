import re
from unittest.mock import patch

import pytest

from fileutil.file_util import FileUtil


@pytest.mark.integration
class TestProjectRootOverride:
    """
    Tests for FileUtil project_root_override behavior.

    Ensures FileUtil can work both in its own repo
    (by marker search) and with an explicit override
    provided by consuming projects.

    tmp_path is a pytest fixture that provides a unique, empty temp directory.
    This simulates an external consuming project defining its root explicitly.
    """

    def test_can_find_file_inside_ebf_util_without_override(self):
        sut = FileUtil()
        file_path = sut.get_file_from_project_root('some_txt_file.txt', search_path=r'tests/fileutil')
        assert sut._project_root_override is None
        assert file_path.exists(), f"some_txt_file.txt does not exist at {file_path}"

    def test_can_find_file_inside_external_project_with_override_in_init(self, tmp_path):
        sut = FileUtil(project_root_override=tmp_path)
        result = sut.get_project_root()
        assert result == tmp_path

    def test_can_find_file_inside_external_project_with_override_in_setter(self, tmp_path):
        sut = FileUtil()
        sut.set_project_root_override(tmp_path)
        result = sut.get_project_root()
        assert result == tmp_path


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

    def test_get_file_from_project_root_base(self, sut):
        file_path = sut.get_file_from_project_root('some_txt_file.txt', search_path='tests/fileutil')
        assert file_path.exists(), f"some_txt_file.txt does not exist at {file_path}"

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
class TestUserBaseStructure:
    @pytest.fixture
    def sut(self) -> FileUtil:
        return FileUtil()

    def test_default_base_dir(self, sut):
        path = str(sut.base_structure)
        assert path.endswith('Investing')

    def test_get_base_dir_when_using_default_base_structure(self, sut):
        path = sut.get_user_base_dir()
        assert str(path).endswith('Investing')

    @pytest.mark.parametrize("filename", ['snapshot.xlsm', 'cagr.xlsm'])  # noqa
    def test_get_file_from_user_base(self, sut, filename):
        path = str(sut.get_file_from_user_base(filename))
        assert path.endswith(filename)

    def test_get_file_from_user_base_when_bad_filename_raises_error(self, sut):
        bad_filename = 'blah'
        base_dir = sut.get_user_base_dir()
        bad_path = re.escape(str(base_dir / bad_filename))
        err_msg = fr"The file {bad_path} does not exist in the {base_dir.name} directory."
        with pytest.raises(FileNotFoundError, match=err_msg):
            sut.get_file_from_user_base(bad_filename)

    @pytest.mark.parametrize("username", ['smith', 'jones'])
    def test_get_user_specific_path_adjust_for_any_user(self, sut, username):
        with patch('os.getlogin', return_value=username):  # noqa
            assert username in str(sut.get_user_specific_path())
