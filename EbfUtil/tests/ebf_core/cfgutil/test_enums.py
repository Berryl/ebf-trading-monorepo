# tests/ebf_core/cfgutil/test_enums.py
import pytest
from enum import Enum, StrEnum, auto

from ebf_core.cfgutil.enums import enum_from_str, normalize_enum_fields
from ebf_core.guards.guards import ContractError


class Color(Enum):
    RED = "red"
    BLUE = "blue"
    GREEN = "green"


class Mode(StrEnum):
    READ_ONLY = auto()      # → "READ_ONLY"
    FULL_ACCESS = auto()    # → "FULL_ACCESS"
    DRY_RUN = auto()        # → "DRY_RUN"


class TestEnumFromStr:
    @pytest.mark.parametrize("input_str, expected",
        [
            ("red", Color.RED),
            ("RED", Color.RED),
            ("Red", Color.RED),
            (" red ", Color.RED),
            ("blue", Color.BLUE),
            ("green", Color.GREEN),
        ],
    )
    def test_case_insensitive(self, input_str, expected):
        assert enum_from_str(input_str, Color) is expected

    @pytest.mark.parametrize(
        "input_str, expected",
        [
            ("read-only", Mode.READ_ONLY),
            ("read_only", Mode.READ_ONLY),
            ("read only", Mode.READ_ONLY),
            ("READ-ONLY", Mode.READ_ONLY),
            ("full-access", Mode.FULL_ACCESS),
            ("dry-run", Mode.DRY_RUN),
        ],
    )
    def test_hyphens_spaces_underscores_are_handled(self, input_str, expected):
        assert enum_from_str(input_str, Mode) is expected

    def test_raises_value_error_on_non_existent_enum_val(self):
        msg = f"'purple' is not a valid Color. Valid options: RED, BLUE, GREEN"

        with pytest.raises(ValueError, match=msg) as exc:
            enum_from_str("purple", Color)

    def test_raises_contract_error_on_none(self):
        with pytest.raises(ContractError, match="Arg 'value' cannot be None"):
            enum_from_str(None, Color)

    def test_raises_value_error_on_empty_string(self):
        with pytest.raises(ContractError):
            enum_from_str("", Color)
        with pytest.raises(ContractError):
            enum_from_str("   ", Color)


class TestNormalizeEnumFields:
    def test_single_field(self):
        data = {"color": "RED"}
        result = normalize_enum_fields(data, "color", Color)
        assert result is not data  # shallow copy
        assert result["color"] is Color.RED

    def test_multiple_fields_same_enum(self):
        data = {"mode": "read-only", "backup_mode": "DRY-RUN"}
        result = normalize_enum_fields(data, ["mode", "backup_mode"], Mode)
        assert result["mode"] is Mode.READ_ONLY
        assert result["backup_mode"] is Mode.DRY_RUN

    def test_missing_field_is_ignored(self):
        data = {"something_else": 42}
        result = normalize_enum_fields(data, "color", Color)
        assert "color" not in result
        assert result["something_else"] == 42

    def test_invalid_value_raises(self):
        data = {"color": "mauve"}
        with pytest.raises(ValueError, match="mauve"):
            normalize_enum_fields(data, "color", Color)

    def test_none_value_raises_contract_error(self):
        data = {"color": None}
        with pytest.raises(ContractError):
            normalize_enum_fields(data, "color", Color)

    def test_mutates_copy_not_original(self):
        original = {"color": "blue"}
        result = normalize_enum_fields(original, "color", Color)
        original["color"] = "still string"
        assert result["color"] is Color.BLUE  # result unchanged