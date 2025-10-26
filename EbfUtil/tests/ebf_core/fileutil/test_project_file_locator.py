import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from ebf_core.fileutil.project_file_locator import ProjectFileLocator

VALID_SEARCH_PATH = r'tests/ebf_core/fileutil'  # noqa


@pytest.fixture
def sut() -> ProjectFileLocator:
    return ProjectFileLocator()


@pytest.mark.integration
class TestProjectRootMember:

    def test_project_root_override_default_is_none(self, sut):
        assert sut._project_root is None

    def test_use_cwd_default_is_false(self, sut):
        assert sut._use_cwd_as_root is False

    def test_when_project_root_override_path_is_set(self, sut, tmp_path):
        expected_root = tmp_path
        sut = ProjectFileLocator(project_root=expected_root)
        assert sut._project_root == expected_root
        assert sut.get_project_root() == expected_root, "project_root s/b project_root_override arg"

    def test_when_project_root_override_is_none_and_use_cwd_flag_is_true(self):
        sut = ProjectFileLocator(use_cwd_as_root=True)
        expected_root = Path.cwd().resolve()
        assert sut._project_root == expected_root
        assert sut.get_project_root() == expected_root, "project_root s/b Path.cwd().resolve()"

    def test_project_root_override_arg_has_precedence_when_use_cwd_flag_is_true(self, tmp_path):
        sut = ProjectFileLocator(use_cwd_as_root=True, project_root=tmp_path)
        expected_root = tmp_path
        assert sut._project_root == expected_root
        assert sut.get_project_root() == expected_root, "project_root s/b the project_root_override arg"

    def test_with_project_root_when_arg_is_path(self, sut, tmp_path):
        assert sut._project_root != tmp_path
        sut.with_project_root(tmp_path)
        assert sut._project_root == tmp_path.resolve()

    def test_with_project_root_when_arg_is_none(self, sut, tmp_path):
        sut = ProjectFileLocator(project_root=tmp_path)
        assert sut._project_root == tmp_path.resolve()

        sut.with_project_root(None)
        assert sut._project_root is None

    def test_with_project_root_when_arg_is_none_and_use_cwd_is_true_from_init(self, sut, tmp_path):
        sut = ProjectFileLocator(project_root=tmp_path, use_cwd_as_root=True)

        sut.with_project_root(None)
        assert sut._project_root == Path.cwd(), "project_root_override should be Path.cwd()"

    def test_with_project_root_when_arg_is_none_and_use_cwd_is_true_from_arg(self, sut, tmp_path):
        sut = ProjectFileLocator(project_root=tmp_path)
        assert sut._use_cwd_as_root is False

        sut.with_project_root(None, use_cwd_as_root=True)
        assert sut._project_root == Path.cwd(), "project_root_override should be Path.cwd()"


@pytest.mark.integration
class TestCachedProjectRoot:

    def test_cache_default_is_none(self, sut):
        assert sut._cached_project_root is None

    def test_cache_is_with_when_use_cache_is_true(self, sut):
        assert sut._cached_project_root is None


@pytest.mark.integration
def test_project_file_locator_logs(caplog):
    # Set up the test to capture logs at DEBUG level
    caplog.set_level(logging.DEBUG, logger='ebf_core.fileutil.project_file_locator')

    # Create the instance and call a method that emits logs
    sut = ProjectFileLocator()
    sut.get_project_root()

    # Verify log output
    assert any("Searching for project root" in record.message for record in caplog.records)
    assert any("Found marker" in record.message or "Using cached project root" in record.message
               for record in caplog.records)


class TestProjectFileLocator:
    def test_property_base_structure(self, sut):
        assert sut.base_structure == Path('Dropbox') / 'Green Olive' / 'Investing', "default base structure path"

        sut = ProjectFileLocator(base_structure=Path('blah'))
        assert sut.base_structure == Path('blah'), "override base structure path"

    @pytest.mark.parametrize('marker', ['.idea', '.git', 'pyproject.toml'])
    def test_property_common_project_markers(self, sut, marker):
        assert marker in sut.common_project_markers

    def test_priority_marker(self, sut):
        assert sut._priority_marker is None

        sut = ProjectFileLocator(priority_marker='blah')
        assert sut._priority_marker == 'blah'


@pytest.mark.integration
class TestGetProjectRoot:

    def test_get_project_root_returns_path_with_at_least_one_common_marker_when_no_args(self, sut):
        found = sut.get_project_root()
        print(found)
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
        p = sut.try_get_file_from_project_root("some_txt_file.txt", search_path=VALID_SEARCH_PATH, )
        assert p is not None and p.exists()

    def test_try_get_project_file_missing_returns_none(self, sut):
        p = sut.try_get_file_from_project_root("does_not_exist.txt")
        assert p is None


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
        assert sut._project_root is None
        assert file_path.exists(), f"some_txt_file.txt does not exist at {file_path}"

    def test_can_find_file_inside_external_project_with_override_in_init(self, tmp_path):
        sut = ProjectFileLocator(project_root=tmp_path)
        result = sut.get_project_root()
        assert result == tmp_path

    def test_can_find_file_inside_external_project_with_override_in_setter(self, tmp_path):
        sut = ProjectFileLocator()
        sut.with_project_root(tmp_path)
        result = sut.get_project_root()
        assert result == tmp_path


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
