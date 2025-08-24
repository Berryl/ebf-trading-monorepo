from typing import Optional

from .cfg_service import ConfigService
from ..fileutil import FileUtil


def load_config(
        app_name: str,
        *,
        project_filename: str,
        user_filename: str,
        file_util: Optional[FileUtil],
        search_path: Optional[str],
        return_sources: bool,
):
    return ConfigService().load(
        app_name,
        project_filename=project_filename,
        user_filename=user_filename,
        file_util=file_util,
        search_path=search_path,
        return_sources=return_sources,
    )


__all__ = ["load_config"]
