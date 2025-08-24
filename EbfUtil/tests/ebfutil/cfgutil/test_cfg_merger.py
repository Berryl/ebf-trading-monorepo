import pytest
from ebfutil.cfgutil.cfg_merger import ConfigMerger


class TestConfigMerger:
    def test_deep_merges_nested_dicts(self):
        tgt = {"a": 1, "nest": {"x": 1, "y": 1}}
        src = {"b": 2, "nest": {"y": 9}}
        out = ConfigMerger.deep(tgt, src)
        assert out == {"a": 1, "b": 2, "nest": {"x": 1, "y": 9}}

    def test_replaces_lists_and_scalars(self):
        tgt = {"list": [1], "v": 1}
        src = {"list": [2], "v": 9}
        out = ConfigMerger.deep(tgt, src)
        assert out == {"list": [2], "v": 9}

    @pytest.mark.parametrize("tgt, src, expected", [
        (None, {"a": 1}, {"a": 1}),
        ({"a": 1}, None, {"a": 1}),
        ({}, {}, {}),
    ])
    def test_handles_none_and_empty(self, tgt, src, expected):
        assert ConfigMerger.deep(tgt, src) == expected
