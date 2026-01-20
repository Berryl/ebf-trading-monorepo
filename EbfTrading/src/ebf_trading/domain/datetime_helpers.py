from datetime import datetime, timedelta, date
from typing import Union, Optional

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