from pathlib import Path

from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class TestPublicApi(ConfigServiceFixture):

    def test_load_config(self, project_file_util, fake_project_file: Path, data: dict, app_name: str):
        from ebfutil.cfgutil import load_config
        cfg, sources = load_config(app_name=app_name, file_util=project_file_util, return_sources=True, )
        assert cfg == data
        assert sources == [fake_project_file]
