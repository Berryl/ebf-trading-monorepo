from ebfutil.cfgutil import ConfigService
from ebfutil.fileutil import FileUtil
from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class TestLoad(ConfigServiceFixture):

    def test_when_no_files_found_at_all(self, sut: ConfigService, mock_file_util: FileUtil, app_name: str):
        mock_file_util.try_get_file_from_project_root.return_value = None
        mock_file_util.try_get_file_from_user_base_dir.return_value = None

        cfg, sources = sut.load(app_name=app_name, return_sources=True, file_util=mock_file_util)

        assert cfg == {}
        assert sources == []
