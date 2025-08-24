import copy
from typing import Mapping

import pytest

from ebfutil.cfgutil.cfg_merger import ConfigMerger


class TestConfigMerger:
    @pytest.fixture
    def sut(self) -> ConfigMerger:
        return ConfigMerger()

    def test_when_nested_dicts(self, sut):
        tgt = {"a": 1, "nest": {"x": 1, "y": 1}}
        src = {"b": 2, "nest": {"y": 9}}
        out = sut.deep(tgt, src)
        assert out == {"a": 1, "b": 2, "nest": {"x": 1, "y": 9}}

    def test_when_lists_and_scalars(self, sut):
        tgt = {"list": [1], "v": 1}
        src = {"list": [2], "v": 9}
        out = sut.deep(tgt, src)
        assert out == {"list": [2], "v": 9}

    @pytest.mark.parametrize("tgt, src, expected", [
        (None, {"a": 1}, {"a": 1}),
        ({"a": 1}, None, {"a": 1}),
        (None, None, {}),
        ({}, {}, {}),
    ])
    def test_none_and_empty_args(self, tgt, src, expected):
        assert ConfigMerger.deep(tgt, src) == expected

    def test_sut_custom_mapping(self, sut):
        class CustomMap(Mapping):
            def __init__(self, data):
                self.data = data

            def __getitem__(self, key):
                return self.data[key]

            def __iter__(self):
                return iter(self.data)

            def __len__(self):
                return len(self.data)

        tgt = {"a": 1}
        src = CustomMap({"a": 2, "b": 3})
        result = sut.deep(tgt, src)
        assert result == {"a": 2, "b": 3}
        assert result is not tgt

    def test_sut_immutability(self, sut):
        tgt = {"a": 1, "b": {"x": 1}}
        src = {"b": {"y": 2}}
        original_tgt = copy.deepcopy(tgt)  # deep copy
        original_src = copy.deepcopy(src)  # deep copy
        result = sut.deep(tgt, src)
        assert tgt == original_tgt
        assert src == original_src
        # optional but useful aliasing check:
        assert result["b"] is not tgt["b"]
