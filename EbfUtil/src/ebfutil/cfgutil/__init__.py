from typing import Optional

from .cfg_service import ConfigService
from ..fileutil import FileUtil


def load_config(*, app_name, project_search_path="config",
                filename=ConfigService.DEFAULT_FILENAME, user_filename=None,
                return_sources=False, file_util=None):
    return ConfigService().load(
        app_name=app_name,
        project_search_path=project_search_path,
        filename=filename,
        user_filename=user_filename,
        return_sources=return_sources,
        file_util=file_util,
    )


__all__ = ["load_config"]
