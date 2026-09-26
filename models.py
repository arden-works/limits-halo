"""Provider-neutral data. Percentages represent remaining allowance."""
from dataclasses import dataclass
from datetime import datetime
import math


@dataclass(frozen=True)
class LimitState:
    five_hour_percent: float | None
    five_hour_reset_at: datetime | None
    weekly_percent: float | None
    weekly_reset_at: datetime | None
    last_updated: datetime

    def __post_init__(self):
        for percent, reset in ((self.five_hour_percent, self.five_hour_reset_at),
                               (self.weekly_percent, self.weekly_reset_at)):
            if (percent is None) != (reset is None):
                raise ValueError("Remaining percentage and reset must both be present or absent")
            if percent is not None and (not math.isfinite(percent) or not 0 <= percent <= 100):
                raise ValueError("Remaining allowance must be a finite percentage between 0 and 100")
        for date in (self.five_hour_reset_at, self.weekly_reset_at, self.last_updated):
            if date is not None and (date.tzinfo is None or date.utcoffset() is None):
                raise ValueError("Dates must be timezone-aware")


def severity(value: float) -> str:
    return "#e68d91" if value <= 5 else "#dba078" if value <= 15 else "#cbb387" if value <= 30 else "#a4b9ca"
