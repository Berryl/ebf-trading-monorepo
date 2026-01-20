from datetime import datetime, date
from zoneinfo import ZoneInfo

from ebf_trading.domain.datetime_helpers import next_friday
from ebf_trading.domain.value_objects.options.expiration_date import ExpirationDate

KNOWN_WEDNESDAY_WITHOUT_TIME = datetime(2001, 9, 11)
KNOWN_WEDNESDAY_WITH_OPEX_TIME = datetime(2001, 9, 11, 17, 30, tzinfo=ZoneInfo("America/New_York"))

KNOWN_FRIDAY_WITHOUT_TIME = datetime(2001, 9, 14)
KNOWN_FRIDAY_WITH_OPEX_TIME = datetime(2001, 9, 14, 17, 30, tzinfo=ZoneInfo("America/New_York"))


class TestExpirationDate:
    def test_can_apply_opex_time_to_any_date(self):
        sut = ExpirationDate(datetime.now())
        result = sut.apply_opex_time_to(KNOWN_WEDNESDAY_WITH_OPEX_TIME)
        assert result.hour == 17
        assert result.minute == 30
        assert result.tzinfo == ZoneInfo("America/New_York")

    def test_can_create_with_any_date(self):
        sut = ExpirationDate(KNOWN_WEDNESDAY_WITHOUT_TIME)
        assert sut.when == KNOWN_WEDNESDAY_WITHOUT_TIME

    def test_is_opex_friday(self):
        assert ExpirationDate(KNOWN_FRIDAY_WITHOUT_TIME).is_friday() is True
        assert ExpirationDate(KNOWN_WEDNESDAY_WITHOUT_TIME).is_friday() is False

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


class TestNextFriday:

    def test_can_get_next_friday_from_past_date(self):
        result = next_friday(KNOWN_WEDNESDAY_WITHOUT_TIME)
        assert result.weekday() == 4

    def test_if_friday_is_passed_then_same_friday_is_return(self):
        result = next_friday(KNOWN_FRIDAY_WITHOUT_TIME)
        assert result == KNOWN_FRIDAY_WITHOUT_TIME
        assert result.weekday() == 4

    def test_when_no_arg(self):
        result = next_friday()
        assert result.weekday() == 4
