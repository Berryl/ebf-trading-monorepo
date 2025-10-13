from __future__ import annotations
from typing import Any
import pytest

import ebf_core.cfgutil as sut
from tests.ebf_core.support.unit_test_helpers_cfg import mocked_cfg_service, expect_load_once


class TestLoadApi:
    def test_delegates_and_passthrough_tuple(self, monkeypatch) -> None:
        cfg: dict[str, Any] = {"k": 1}
        sources = ["/p.yml", "/u.yml"]
        m = mocked_cfg_service(monkeypatch, sut, return_value=(cfg, sources))

        out = sut.load_config(
            app_name="app",
            project_search_path="config",
            filename="p.yml",
            user_filename="u.yml",
            return_sources=True,
            file_util=None,
        )

        assert out == (cfg, sources)
        expect_load_once(
            m,
            "app",
            project_search_path="config",
            filename="p.yml",
            user_filename="u.yml",
            return_sources=True,
            file_util=None,
        )

    def test_delegates_and_passthrough_cfg_only(self, monkeypatch) -> None:
        cfg: dict[str, Any] = {"nested": {"x": 2}}
        m = mocked_cfg_service(monkeypatch, sut, return_value=cfg)

        out = sut.load_config(app_name="app", filename=None, user_filename="u.yml", return_sources=False)

        assert out == cfg
        expect_load_once(
            m,
            "app",
            project_search_path="config",
            filename=None,
            user_filename="u.yml",
            return_sources=False,
            file_util=None,
        )

    def test_propagates_exception(self, monkeypatch) -> None:
        m = mocked_cfg_service(monkeypatch, sut, side_effect=RuntimeError("boom"))

        with pytest.raises(RuntimeError, match="boom"):
            sut.load_config(app_name="app", filename="p.yml")

        # optional: ensure it actually tried the call
        expect_load_once(
            m,
            "app",
            project_search_path="config",
            filename="p.yml",
            user_filename=None,
            return_sources=False, # default value
            file_util=None,
        )
