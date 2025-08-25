from typing import Optional

from .cfg_service import ConfigService
from ..fileutil import FileUtil


def load_config(
        app_name: str,
        *,
        project_filename: str,
        user_filename: str,
        file_util: Optional[FileUtil],
        project_search_path: Optional[str],
        return_sources: bool,
):
    return ConfigService().load(app_name, project_search_path=project_search_path, project_filename=project_filename,
                                user_filename=user_filename, return_sources=return_sources, file_util=file_util)


__all__ = ["load_config"]
