from datetime import datetime, timedelta, date, time
from typing import Union, Optional
from zoneinfo import ZoneInfo

OPEX_TIME_ET_NAIVE = time(16, 0)                           # 4:00 PM – use this most often
OPEX_TZ = ZoneInfo("America/New_York")

def opex_time()-> time:
    ## 4 PM
    return time(16, 0, tzinfo=ZoneInfo("America/New_York"))

def next_friday(from_date: Optional[Union[date, datetime]] = None) -> datetime:
    """
    Returns the next Friday as a datetime object (at 00:00:00).
    If today is Friday, returns today at midnight.

    Args:
        from_date: Optional date or datetime to start from.
                   Defaults to the current local date.

    Returns:
        datetime: The next Friday (or today if Friday) at 00:00:00
    """
    # Normalize to date
    if from_date is None:
        base_date = datetime.now().date()
    elif isinstance(from_date, datetime):
        base_date = from_date.date()
    else:
        base_date = from_date

    # Calculate days to next Friday (0 if today is Friday)
    weekday = base_date.weekday()          # 0 = Mon ... 4 = Fri ... 6 = Sun
    days_to_add = (4 - weekday) % 7

    next_friday_date = base_date + timedelta(days=days_to_add)

    # Return as datetime at midnight
    return datetime.combine(next_friday_date, datetime.min.time())


def next_options_expiration(
        from_date: Optional[Union[date, datetime]] = None,
        *,
        use_aware_time: bool = False
) -> datetime:
    """
    Returns the next standard options expiration datetime (usually 3rd Friday)
    at 4:00 PM ET.

    For simplicity this uses next Friday — replace with third_friday logic
    if you need actual monthly/weekly expiration detection.
    """
    next_fri_midnight = next_friday(from_date)
    t = OPEX_TIME_ET_AWARE if use_aware_time else OPEX_TIME_ET_NAIVE

    dt = datetime.combine(next_fri_midnight.date(), t)

    # If you used naive time → attach timezone now
    if not use_aware_time:
        dt = dt.replace(tzinfo=OPEX_TZ)

    return dt