from pathlib import Path

from ebfutil.cfgutil import ConfigService
from tests.ebfutil.cfgutil.fixtures.cfg_svc_fixture import ConfigServiceFixture


class TestYamlSpecific(ConfigServiceFixture):
    def test_comments_are_ignored(self, sut: ConfigService, project_fu, project_root: Path, app_name: str):
        p = project_root / "config" / "with_comments.yaml"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# top comment\nbase: 1\nnest:\n  k: v  # inline\n",
            encoding="utf-8",
        )
        cfg = sut.load(app_name=app_name, filename="with_comments.yaml", file_util=project_fu)
        assert cfg == {"base": 1, "nest": {"k": "v"}}
