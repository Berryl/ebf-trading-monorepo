from datetime import datetime
from zoneinfo import ZoneInfo

from ebf_trading.domain.value_objects.options.expiration_date import ExpirationDate

KNOWN_WEDNESDAY_WITHOUT_TIME = datetime(2001, 9, 11)
KNOWN_WEDNESDAY_WITH_OPEX_TIME = datetime(2001, 9, 11, 17,30, tzinfo=ZoneInfo("America/New_York"))

KNOWN_FRIDAY_WITHOUT_TIME = datetime(2001, 9, 13)
KNOWN_FRIDAY_WITH_OPEX_TIME = datetime(2001, 9, 13, 17,30, tzinfo=ZoneInfo("America/New_York"))

class TestExpirationDate:
    def test__can_create_with_any_date(self):
        sut = ExpirationDate(KNOWN_WEDNESDAY_WITHOUT_TIME)
        assert sut.when == KNOWN_WEDNESDAY_WITHOUT_TIME

    def test_is_opex_friday(self):
        pass

    def test_to_occ_fmt(self):
        sut = ExpirationDate(KNOWN_WEDNESDAY_WITHOUT_TIME)
        result = sut.to_occ_fmt()
        assert result == '010911'

    def test_from_occ_fmt(self):
        pass
        # match fnt:
        #     case OptionFormat.OCC | OptionFormat.OCC_SANS_PADDING:
        #         g.ensure_str_exact_length(s, 6, "expiration date")
        #     case _:
        #         raise ValueError(f"Unknown format: {fnt}")
        # try:
        #     year = int(s[0:2]) + 2000  # YY -> YYYY
        #     month = int(s[2:4])
        #     day = int(s[4:6])
        #     return datetime(year, month, day)
        # except (ValueError, IndexError) as e:
        #     raise ValueError(f"Invalid expiration date in OCC ticker: {s}") from e
