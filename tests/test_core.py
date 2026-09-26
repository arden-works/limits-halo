import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from unittest.mock import patch
import paths
from models import LimitState, severity
from time_helpers import format_remaining_time, format_reset_display
from settings import Config
from providers.mock import MockLimitProvider
from windows.taskbar import Taskbar, free_slot


class CoreTests(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(len({severity(n) for n in (5, 12, 22, 72)}), 4)
        self.assertEqual(severity(0), severity(5))
        self.assertEqual(severity(6), severity(15))
        self.assertEqual(severity(16), severity(30))
        self.assertEqual(severity(31), severity(100))

    def test_dates_and_invalid_data(self):
        now = datetime.now(timezone.utc)
        for value in (-1, 101, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                LimitState(value, now, 0, now, now)
        with self.assertRaises(ValueError):
            LimitState(0, datetime.now(), 0, now, now)
        self.assertEqual(format_remaining_time(now + timedelta(hours=2, minutes=14), now), "Resets: 02:14")
        self.assertEqual(format_remaining_time(now - timedelta(seconds=1), now), "Resetting…")
        self.assertEqual(format_remaining_time(now + timedelta(seconds=1), now), "Resets: 1m")

    def test_countdown_matrix(self):
        now = datetime(2026, 9, 24, 12, tzinfo=timezone(timedelta(hours=3)))
        cases = [(5, "5m", "5m"), (59, "59m", "59m"), (65, "01:05", "1h 05m"),
                 (299, "04:59", "4h 59m"), (1380, "23:00", "23h 00m"),
                 (1440, "24:00", "1d 00h 00m"), (3060, "51:00", "2d 03h 00m"),
                 (10020, "167:00", "6d 23h 00m")]
        for minutes, short, week in cases:
            date = (now + timedelta(minutes=minutes)).astimezone(timezone.utc)
            self.assertEqual(format_remaining_time(date, now), "Resets: " + short)
            self.assertEqual(format_remaining_time(date, now, "weekly"), "Resets: " + week)
        future = now + timedelta(days=2, hours=3, minutes=17)
        self.assertEqual(format_remaining_time(future, now, "weekly", True), "Resets: 2d 3h")
        self.assertEqual(format_remaining_time(future, future), "Resetting…")
        self.assertEqual(format_remaining_time(future, now + timedelta(hours=1), "weekly"), "Resets: 2d 02h 17m")
        self.assertEqual(format_remaining_time(now + timedelta(hours=1), now - timedelta(hours=1)), "Resets: 02:00")
        with self.assertRaises(ValueError):
            format_remaining_time(datetime.now(), now)
        with self.assertRaises(ValueError):
            format_remaining_time(now, datetime.now())

    def test_mock_reset_and_presets(self):
        provider = MockLimitProvider()
        for percent in (5, 40, 72, 88, 97, 100, 5):
            provider.cycle()
            state = provider.get_state()
            self.assertEqual((state.five_hour_percent, state.weekly_percent), (percent, percent))
        provider.five_reset = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.assertEqual(provider.get_state().five_hour_percent, 100)

    def test_placement_and_collisions(self):
        taskbar = Taskbar(1, 0, 1032, 1920, 1080, 1, (0, 0, 1920, 1080))
        self.assertEqual(free_slot(taskbar, [(665, 1256)], 20, 470), (20, 470))
        self.assertEqual(free_slot(taskbar, [(0, 160), (665, 1256)], 20, 470), (168, 470))
        self.assertEqual(free_slot(taskbar, [(340, 1256)], 20, 470), (20, 312))
        self.assertIsNone(free_slot(taskbar, [(210, 1256)], 20, 470))
        self.assertEqual(free_slot(taskbar, [], 20, 470, 300), (20, 280))
        scaled = Taskbar(2, -2560, 1380, 0, 1440, 1.5, (-2560, 0, 0, 1440))
        self.assertEqual(free_slot(scaled, [(-1560, -500)], 20, 470), (-2530, 705))

    def test_config_rejects_bad_types(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "config.json"
            for content in ('{"opacity":2}', '{"width":true}', '{"show_countdown":"yes"}',
                            '{"clock_format":13}', '{"reset_display":"soon"}',
                            '{"notification_color":"unknown"}', '{"compact_view":1}',
                            '{"font_scale":90}', '{"font_scale":true}',
                            '{"language":"fr"}', '{"show_five_hour":false,"show_weekly":false}',
                            '{"safe_right_x":-1}', '{"mystery":0}', '[]'):
                path.write_text(content)
                with self.assertRaises(ValueError):
                    Config.load(path)

    def test_example_config_initializes_only_when_local_config_is_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / "config.example.json").write_text('{"language":"en"}', encoding="utf-8")
            with patch.object(paths, "RESOURCE_DIR", directory), patch.object(paths, "data_dir", return_value=directory):
                local = paths.config_path()
                self.assertEqual(Config.load(local).language, "en")
                local.write_text('{"language":"tr"}', encoding="utf-8")
                self.assertEqual(paths.config_path().read_text(encoding="utf-8"), '{"language":"tr"}')

    def test_reset_display_uses_local_clock(self):
        local = timezone(timedelta(hours=3))
        now = datetime(2026, 9, 25, 23, 30, tzinfo=local)
        reset = datetime(2026, 9, 26, 1, 5, tzinfo=local).astimezone(timezone.utc)
        self.assertEqual(format_reset_display(reset, now, display="in"), "Reset: 01:35")
        local_reset = reset.astimezone()
        date = f"{local_reset.day:02d} {local_reset.strftime('%b')} "
        self.assertEqual(format_reset_display(reset, now, mode="five_hour", display="at", clock_format=24),
                         f"Resets at {local_reset.hour:02d}:{local_reset.minute:02d}")
        self.assertEqual(format_reset_display(reset, now, mode="five_hour", display="at", clock_format=24,
                                              compact=True, language="tr"),
                         f"Sıfırlanır {local_reset.hour:02d}:{local_reset.minute:02d}")
        self.assertEqual(format_reset_display(reset, now, mode="weekly", display="at", clock_format=24),
                         f"Resets at {date}{local_reset.hour:02d}:{local_reset.minute:02d}")
        hour = local_reset.hour % 12 or 12
        marker = "AM" if local_reset.hour < 12 else "PM"
        self.assertEqual(format_reset_display(reset, now, mode="five_hour", display="at", clock_format=12),
                         f"Resets at {hour}:{local_reset.minute:02d} {marker}")
        self.assertEqual(format_reset_display(reset, now, mode="weekly", display="at", clock_format=12),
                         f"Resets at {date}{hour}:{local_reset.minute:02d} {marker}")
        self.assertEqual(format_reset_display(reset, now, mode="weekly", display="at", clock_format=24,
                                              compact=True),
                         f"{local_reset.day:02d}/{local_reset.month:02d} "
                         f"{local_reset.hour:02d}:{local_reset.minute:02d}")
        self.assertEqual(format_reset_display(reset, now, display="in", language="tr"),
                         "Reset: 01:35")


if __name__ == "__main__":
    unittest.main()
