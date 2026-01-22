# tests/test_string_helpers.py
from __future__ import annotations

import random
import string

import pytest

from ebf_core.miscutil.string_helpers import (
    clean_string,
    is_str_valued,
    pluralize_word,
    random_string,
)


class TestPluralizeWord:
    def test_singular_when_count_is_one(self) -> None:
        assert pluralize_word(1, "cat") == "cat"
        assert pluralize_word(1, "person") == "person"
        assert pluralize_word(1, "octopus") == "octopus"

    def test_plural_when_count_is_not_one(self) -> None:
        assert pluralize_word(0, "cat") == "cats"
        assert pluralize_word(2, "cat") == "cats"
        assert pluralize_word(5, "cat") == "cats"

    def test_irregular_nouns(self) -> None:
        assert pluralize_word(1, "child") == "child"
        assert pluralize_word(3, "child") == "children"

        assert pluralize_word(1, "person") == "person"
        assert pluralize_word(10, "person") == "people"

        assert pluralize_word(1, "sheep") == "sheep"
        assert pluralize_word(100, "sheep") == "sheep"

        assert pluralize_word(1, "mouse") == "mouse"
        assert pluralize_word(99, "mouse") == "mice"

    def test_with_show_count(self) -> None:
        assert pluralize_word(1, "dog", show_count=True) == "1 dog"
        assert pluralize_word(5, "dog", show_count=True) == "5 dogs"
        assert pluralize_word(0, "cat", show_count=True) == "0 cats"


class TestCleanString:
    def test_none_returns_empty(self) -> None:
        assert clean_string(None) == ""

    def test_empty_string_returns_empty(self) -> None:
        assert clean_string("") == ""

    def test_whitespace_only_returns_empty(self) -> None:
        assert clean_string("   \t\n\r") == ""

    def test_trims_surrounding_whitespace(self) -> None:
        assert clean_string("  hello world  ") == "hello world"
        assert clean_string("\tfoo\n") == "foo"


class TestIsStrValued:
    @pytest.mark.parametrize("value", [None, "", "   ", "\t\n", " \r\n "],)
    def test_returns_false_for_non_valued(self, value: str | None) -> None:
        assert is_str_valued(value) is False

    def test_returns_false_for_empty_string(self) -> None:
        assert is_str_valued(self) is False

    @pytest.mark.parametrize("value", ["hello", "  hi  ", "0", "false", " None "],)
    def test_returns_true_for_valued_strings(self, value: str) -> None:
        assert is_str_valued(value) is True


class TestRandomString:
    def test_default_length_is_8(self) -> None:
        assert len(random_string()) == 8

    def test_custom_length(self) -> None:
        assert len(random_string(15)) == 15
        assert len(random_string(1)) == 1

    def test_uses_only_ascii_letters_by_default(self) -> None:
        s = random_string(100)
        assert all(c in string.ascii_letters for c in s)

    def test_returns_different_values(self) -> None:
        # The probability of collision is astronomically low
        assert random_string(20) != random_string(20)

    def test_is_reproducible_with_seed(self) -> None:
        random.seed(12345)
        a = random_string(12)
        random.seed(12345)
        b = random_string(12)
        assert a == b
