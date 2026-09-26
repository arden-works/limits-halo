import unittest
import subprocess
import sys
import threading
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from models import LimitState
from providers.codex import CodexLimitProvider, map_rate_limits
from windows import codex_launcher


def window(minutes, percent=25, reset=1790000000):
    return {"windowDurationMins": minutes, "usedPercent": percent, "resetsAt": reset}


class CodexTests(unittest.TestCase):
    def test_maps_two_windows_independent_of_order(self):
        result = {"rateLimitsByLimitId": {"codex": {
            "limitId": "codex", "primary": window(10080, 42), "secondary": window(300, 12)}}}
        state = map_rate_limits(result)
        self.assertEqual((state.five_hour_percent, state.weekly_percent), (88, 58))
        self.assertEqual(state.five_hour_reset_at, datetime.fromtimestamp(1790000000, timezone.utc))

    def test_missing_window_remains_unavailable(self):
        state = map_rate_limits({"rateLimits": {"limitId": "codex", "primary": window(10080, 11)}})
        self.assertIsNone(state.five_hour_percent)
        self.assertEqual(state.weekly_percent, 89)
        self.assertIsNone(state.five_hour_reset_at)
        with self.assertRaises(ValueError):
            LimitState(10, None, 11, state.weekly_reset_at, state.last_updated)

    def test_invalid_and_wrong_bucket_rejected(self):
        for result in (
            {"rateLimits": {"limitId": "codex_other", "primary": window(300)}},
            {"rateLimits": {"limitId": "codex", "primary": window(300, True)}},
            {"rateLimits": {"limitId": "codex", "primary": window(60)}},
        ):
            with self.assertRaises(ValueError):
                map_rate_limits(result)

    def test_repeated_launch_click_is_suppressed(self):
        with patch.object(codex_launcher, "find_codex_window", return_value=None), \
             patch.object(codex_launcher, "launch_codex") as launch:
            codex_launcher._last_launch = 0
            codex_launcher.toggle_codex_window()
            codex_launcher.toggle_codex_window()
            self.assertEqual(launch.call_count, 1)

    def test_provider_close_reaps_child_and_reader(self):
        provider = CodexLimitProvider(executable=sys.executable)
        process = subprocess.Popen([sys.executable, "-u", "-c", "import time; time.sleep(30)"],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL)
        provider.process = process
        reader = threading.Thread(target=lambda: list(process.stdout), daemon=True)
        provider.reader = reader
        reader.start()
        provider.close()
        self.assertIsNotNone(process.poll())
        self.assertTrue(process.stdout.closed)
        self.assertFalse(reader.is_alive())

    def test_stopping_provider_never_starts_child(self):
        provider = CodexLimitProvider(executable="codex.exe")
        provider.stop_new_work()
        with patch("providers.codex.subprocess.Popen") as popen:
            with self.assertRaises(RuntimeError):
                provider.get_state()
            popen.assert_not_called()

    def test_missing_five_hour_hides_its_layout_block(self):
        from PySide6.QtWidgets import QApplication
        from widget import responsive_layout
        app = QApplication.instance() or QApplication([])
        now = datetime.now(timezone.utc)
        state = LimitState(None, None, 12, now + timedelta(days=3), now)
        for width, height in ((500, 48), (240, 48), (240, 32)):
            blocks, divider, fits, stacked = responsive_layout(width, height, state)
            self.assertTrue(fits)
            self.assertEqual(len(blocks), 1)
            self.assertEqual(blocks[0]["index"], 1)
            self.assertIsNone(divider)


if __name__ == "__main__":
    unittest.main()
