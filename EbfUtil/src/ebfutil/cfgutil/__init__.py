from .cfg_service import ConfigService


def load_config(
        *, app_name, project_search_path: str = "config",
        filename=ConfigService.DEFAULT_FILENAME, user_filename=None, return_sources=False, file_util=None
):
    return ConfigService().load(app_name,
                                project_search_path=project_search_path,
                                filename=filename,
                                user_filename=user_filename,
                                return_sources=return_sources,
                                file_util=file_util,
                                )


def store_config(cfg: dict, *, app_name, project_search_path: str = "config",
                 filename: str = ConfigService.DEFAULT_FILENAME,
                 user_filename: str | None = None,
                 target: str = "user",
                 file_util=None):
    """
    Persist a config mapping via ConfigService.store and return the written Path.
    """
    return ConfigService().store(cfg, app_name,
                                 project_search_path=project_search_path,
                                 filename=filename,
                                 user_filename=user_filename,
                                 target=target,
                                 file_util=file_util,
                                 )


__all__ = ["load_config"]
