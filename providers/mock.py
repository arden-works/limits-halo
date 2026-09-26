from datetime import datetime, timedelta, timezone
from threading import Lock
from models import LimitState
from providers.base import LimitProvider


class MockLimitProvider(LimitProvider):
    name = "Mock data"
    is_mock = True
    presets = (5, 40, 72, 88, 97, 100)

    def __init__(self, five_hour=72, weekly=31):
        self._lock = Lock()
        self.five_hour, self.weekly = five_hour, weekly
        now = datetime.now(timezone.utc)
        self.five_reset = now + timedelta(hours=2, minutes=14)
        self.week_reset = now + timedelta(days=3, hours=7)
        self.index = -1

    def cycle(self):
        with self._lock:
            self.index = (self.index + 1) % len(self.presets)
            self.five_hour = self.weekly = self.presets[self.index]

    def get_state(self):
        with self._lock:
            now = datetime.now(timezone.utc)
            if now >= self.five_reset:
                self.five_reset = now + timedelta(hours=5)
                self.five_hour = 100
            if now >= self.week_reset:
                self.week_reset = now + timedelta(days=7)
                self.weekly = 100
            return LimitState(self.five_hour, self.five_reset, self.weekly, self.week_reset, now)
