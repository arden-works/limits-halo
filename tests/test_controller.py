import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from controller import Controller
from providers.mock import MockLimitProvider
from settings import Config
from widget import LimitWidget


class FakeEvents(QObject):
    stacking_changed = Signal()
    geometry_changed = Signal()
    buttons_changed = Signal()
    clock_changed = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self.taskbar_hwnd = 0
        self.closed = False

    def close(self):
        self.closed = True


class SlowProvider:
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.finished = False
        self.closed = False

    def get_state(self):
        self.started.set()
        self.release.wait(5)
        self.finished = True
        return MockLimitProvider().get_state()

    def close(self):
        assert self.finished, "provider closed while get_state was running"
        self.closed = True

    def stop_new_work(self):
        pass


class ControllerLifecycleTests(unittest.TestCase):
    def test_stop_waits_for_provider_and_prevents_new_work(self):
        app = QApplication.instance() or QApplication([])
        provider = SlowProvider()
        widget = LimitWidget(Config(), is_mock=False)
        with tempfile.TemporaryDirectory() as temp:
            watcher = type("Watcher", (), {"path": Path(temp) / "missing.db", "check": lambda self: False})()
            with patch("controller.ShellEvents", FakeEvents), \
                 patch("controller.CodexNotificationWatcher", return_value=watcher), \
                 patch("controller.discover", return_value=None):
                controller = Controller(widget, provider, Config())
                try:
                    self.assertTrue(provider.started.wait(2))
                    stopped = []
                    controller.stop(lambda: stopped.append(True))
                    self.assertFalse(provider.closed)
                    worker_count = len(controller._workers)
                    controller.refresh()
                    controller.check_notifications()
                    self.assertEqual(len(controller._workers), worker_count)
                    provider.release.set()
                    deadline = time.monotonic() + 3
                    while not stopped and time.monotonic() < deadline:
                        app.processEvents()
                        time.sleep(.01)
                    self.assertEqual(stopped, [True])
                    self.assertTrue(provider.closed)
                    self.assertTrue(controller.events.closed)
                finally:
                    provider.release.set()
                    widget.close()


if __name__ == "__main__":
    unittest.main()
