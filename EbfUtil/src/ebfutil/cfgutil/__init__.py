from .cfg_service import ConfigService


def load_config(
        app_name: str,
        *,
        file_util=None,
        search_path=None,
        filename: str = "config.yaml",
        return_sources: bool = False,
):
    return ConfigService().load(
        app_name,
        file_util=file_util,
        search_path=search_path,
        project_filename=filename,
        return_sources=return_sources,
    )


__all__ = ["load_config"]
