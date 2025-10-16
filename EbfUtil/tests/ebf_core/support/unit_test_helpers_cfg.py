from __future__ import annotations
from typing import Any
from unittest.mock import create_autospec

from ebf_core.cfgutil import ConfigService


def mocked_cfg_service(monkeypatch, sut, *, return_value: Any = None, side_effect: BaseException | None = None):
    svc_mock = create_autospec(ConfigService, spec_set=True)
    if side_effect is not None:
        # i.e., we want to raise an exception
        svc_mock.load.side_effect = side_effect
    else:
        svc_mock.load.return_value = return_value

    # patch the symbol where it’s looked up (sut.ConfigService), not
    # the global class, because sut.load_config does ConfigService() internally.
    monkeypatch.setattr(sut, "ConfigService", lambda  *_a, **_k: svc_mock)
    return svc_mock

def assert_load_called_once_with_args(m, app_name: str, **kwargs):
    assert m.load.call_args == ((app_name,), kwargs)
