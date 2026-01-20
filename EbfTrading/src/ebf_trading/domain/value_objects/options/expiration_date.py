from dataclasses import dataclass, field
from datetime import datetime, time
from zoneinfo import ZoneInfo

from ebf_core.guards import guards as g


@dataclass(frozen=True)
class ExpirationDate:
    when: datetime
    make__opex_time: bool = True
    opex_time: time = field(default_factory=lambda: time(17, 30))
    opex_tz: ZoneInfo = field(default_factory=lambda: ZoneInfo("America/New_York"))


    def to_occ_fmt(self):
        g.ensure_not_none(self.when, "when")
        return self.when.strftime('%y%m%d')

    def is_friday(self):
        return self.when.weekday() == 4