from __future__ import annotations
from typing import Any
import pytest

import ebf_core.cfgutil as sut
from tests.ebf_core.support.unit_test_helpers_cfg import mocked_cfg_service, assert_load_called_once_with_args

"""
Tests for the public API of the ConfigService.
For functionality tests, see the test_service.py.
All we are testing here is that the API delegates correctly to the service.
"""

class TestLoadConfig:

    def test_calls_svc_and_returns_cfg_only_when_return_sources_is_false(self, monkeypatch) -> None:
        cfg: dict[str, Any] = {"nested": {"x": 2}}
        m = mocked_cfg_service(monkeypatch, sut, return_value=cfg)

        result = sut.load_config(app_name="app", filename=None, user_filename="user.yml", return_sources=False)

        assert result == cfg
        assert_load_called_once_with_args(
            m,
            "app",
            project_search_path="config",
            filename=None,
            user_filename="user.yml",
            return_sources=False,
            file_util=None,
        )

    def test_calls_svc_and_returns_sources_also_when_return_sources_is_true(self, monkeypatch) -> None:
        cfg: dict[str, Any] = {"k": 1}
        sources = ["/project.yml", "/user.yml"]
        m = mocked_cfg_service(monkeypatch, sut, return_value=(cfg, sources))

        result = sut.load_config(app_name="app", project_search_path="config", filename="project.yml",
            user_filename="user.yml",
            return_sources=True,
            file_util=None,
        )

        assert result == (cfg, sources)
        assert_load_called_once_with_args(
            m,
            "app",
            project_search_path="config",
            filename="p.yml",
            user_filename="user.yml",
            return_sources=True,
            file_util=None,
        )

    def test_propagates_exception(self, monkeypatch) -> None:
        m = mocked_cfg_service(monkeypatch, sut, side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            sut.load_config(app_name="app", filename="p.yml")

        # optional: ensure it actually tried the call
        assert_load_called_once_with_args(
            m,
            "app",
            project_search_path="config",
            filename="p.yml",
            user_filename=None,
            return_sources=False, # default value
            file_util=None,
        )
