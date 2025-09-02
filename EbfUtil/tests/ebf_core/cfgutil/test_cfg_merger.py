import copy
from collections.abc import Mapping

import pytest

from ebf_core.cfgutil.cfg_merger import ConfigMerger


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

    def test_custom_mapping(self, sut):
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

    def test_immutability(self, sut):
        tgt = {"a": 1, "b": {"x": 1}}
        src = {"b": {"y": 2}}
        original_tgt = copy.deepcopy(tgt)  # deep copy
        original_src = copy.deepcopy(src)  # deep copy
        result = sut.deep(tgt, src)
        assert tgt == original_tgt
        assert src == original_src
        # optional but useful aliasing check:
        assert result["b"] is not tgt["b"]

    def test_result_is_new_obj_without_alias(self, sut):
        tgt = {"a": {"x": 1}}
        src = {"a": {"y": 2}}
        out = sut.deep(tgt, src)
        assert out is not tgt
        assert out["a"] is not tgt["a"]
        assert out["a"] is not src["a"]

    def test_deeply_nested_dicts(self, sut):
        tgt = {"a": {"b": {"c": 1, "d": 2}}, "k": 0}
        src = {"a": {"b": {"d": 99, "e": 3}}}
        out = sut.deep(tgt, src)
        assert out == {"a": {"b": {"c": 1, "d": 99, "e": 3}}, "k": 0}


class TestEmptyVsNonEmptyMerges:
    @pytest.fixture
    def sut(self) -> ConfigMerger:
        return ConfigMerger()

    def test_merge_with_empty_src(self, sut):
        tgt = {"a": 1, "b": {"x": 1}}
        src = {}
        out = sut.deep(tgt, src)
        assert out == {"a": 1, "b": {"x": 1}}

    def test_merge_with_empty_tgt(self, sut):
        tgt = {}
        src = {"a": 1, "b": {"x": 1}}
        out = sut.deep(tgt, src)
        assert out == {"a": 1, "b": {"x": 1}}

    def test_merge_with_nested_empty_src(self, sut):
        tgt = {"a": {"x": 1, "y": 2}, "k": 0}
        src = {"a": {}}
        out = sut.deep(tgt, src)
        assert out == {"a": {"x": 1, "y": 2}, "k": 0}
