from dataclasses import dataclass
from datetime import datetime
from ebf_core.guards import guards as g


@dataclass(frozen=True)
class ExpirationDate:
    when: datetime

    def to_occ_fmt(self):
        g.ensure_not_none(self.when, "when")
        return self.when.strftime('%y%m%d')