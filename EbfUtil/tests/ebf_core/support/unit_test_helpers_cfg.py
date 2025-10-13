from __future__ import annotations
from typing import Any
from unittest.mock import create_autospec

from ebf_core.cfgutil import ConfigService


def mocked_cfg_service(monkeypatch, sut, *, return_value: Any = None, side_effect: Exception | None = None):
    m = create_autospec(ConfigService, spec_set=True)
    if side_effect is not None:
        m.load.side_effect = side_effect
    else:
        m.load.return_value = return_value
    monkeypatch.setattr(sut, "ConfigService", lambda: m)
    return m

def expect_load_once(m, app_name: str, **kwargs):
    assert m.load.call_args == ((app_name,), kwargs)
