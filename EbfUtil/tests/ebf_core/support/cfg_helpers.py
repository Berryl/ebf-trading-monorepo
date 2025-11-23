# tests/cfg_helpers.py
from pathlib import Path
from shutil import copytree
from types import SimpleNamespace

from ebf_core.cfgutil import ConfigService
from ebf_core.fileutil import ProjectFileLocator


# This is your real shared test data — keep it exactly as you have it
REAL_RESOURCES = Path(__file__).parent / "resources"


def cfg_test_env(tmp_path: Path, *, app_name: str = "myapp") -> SimpleNamespace:
    project_root = tmp_path / "project"
    user_home    = tmp_path / "home"

    service = ConfigService()
    fu = ProjectFileLocator(project_root=project_root, user_base_dir=user_home)

    def use_real_project_config(subdir: str = "config"):
        """Copy the real config.yaml / settings.yaml from resources into project"""
        src = REAL_RESOURCES / subdir
        dst = project_root / subdir
        if src.exists():
            copytree(src, dst, dirs_exist_ok=True)
        return dst

    def use_real_user_config(override_file: str | None = None):
        """Copy a real user config file into ~/.config/myapp/"""
        user_dir = user_home / ".config" / app_name
        user_dir.mkdir(parents=True, exist_ok=True)

        if override_file:
            src = REAL_RESOURCES / override_file
            (user_dir / override_file).write_text(src.read_text())
        else:
            # default: copy everything (or just config.yaml if you prefer)
            src = REAL_RESOURCES
            copytree(src, user_dir, dirs_exist_ok=True)

    return SimpleNamespace(
        service=service,
        fu=fu,
        project_root=project_root,
        user_home=user_home,
        app=app_name,
        use_real_project_config=use_real_project_config,
        use_real_user_config=use_real_user_config,
    )