"""Low-frequency shell checks and non-blocking provider/accessibility work."""
import logging
import threading
import time
from PySide6.QtCore import QObject, Signal, QTimer, QFileSystemWatcher
from PySide6.QtGui import QWindow
from windows.taskbar import (discover, free_slot, is_own_window,
                             apply_overlay_style, get_parent, place_on_taskbar)
from windows.accessibility import button_bounds
from windows.events import ShellEvents
from windows.notifications import CodexNotificationWatcher


class Controller(QObject):
    data_ready = Signal(object, object)
    bounds_ready = Signal(object, object)
    notification_ready = Signal(object, object)
    config_changed = Signal(object)

    def __init__(self, widget, provider, config):
        super().__init__(widget)
        self.widget, self.provider, self.config = widget, provider, config
        self.stopping = False
        self._workers = []
        self._stopped_callback = None
        self._stop_timer = QTimer(self)
        self._stop_timer.setInterval(50)
        self._stop_timer.timeout.connect(self._finish_stop)
        self.taskbar = None
        self.taskbar_window = None
        self.occupied = None
        self.bounds_busy = self.provider_busy = False
        self.notification_busy = False
        self.notification_error_reported = False
        self.notification_watcher = CodexNotificationWatcher()
        self.next_bounds = 0
        self.events = ShellEvents(self)
        self.stack_timer = QTimer(self)
        self.stack_timer.setSingleShot(True)
        self.stack_timer.timeout.connect(self.ensure_stacking)
        self.geometry_timer = QTimer(self)
        self.geometry_timer.setSingleShot(True)
        self.geometry_timer.timeout.connect(self.reposition)
        self.buttons_timer = QTimer(self)
        self.buttons_timer.setSingleShot(True)
        self.buttons_timer.timeout.connect(self.refresh_bounds)
        self.events.stacking_changed.connect(self.schedule_stacking)
        self.events.geometry_changed.connect(self.schedule_geometry)
        self.events.buttons_changed.connect(self.schedule_bounds)
        self.events.clock_changed.connect(widget.refresh_countdown)
        widget.layout_changed.connect(self.schedule_geometry)
        self.data_ready.connect(self.receive_data)
        self.bounds_ready.connect(self.receive_bounds)
        self.notification_ready.connect(self.receive_notification)
        widget.cycle_requested.connect(self.cycle)
        self.shell_timer = QTimer(self)
        # Recovery only; z-order is repaired by native events, never this timer.
        self.shell_timer.setInterval(15_000)
        self.shell_timer.timeout.connect(self.reposition)
        self.shell_timer.start()
        self.provider_timer = QTimer(self)
        self.provider_timer.setInterval(60_000)
        self.provider_timer.timeout.connect(self.refresh)
        self.provider_timer.start()
        self.notification_timer = QTimer(self)
        self.notification_timer.setInterval(1_000)
        self.notification_timer.timeout.connect(self.check_notifications)
        self.notification_timer.start()
        self.notification_files = QFileSystemWatcher(self)
        self.notification_files.fileChanged.connect(self.schedule_notification_check)
        self.notification_files.directoryChanged.connect(self.schedule_notification_check)
        self.notification_debounce = QTimer(self)
        self.notification_debounce.setSingleShot(True)
        self.notification_debounce.timeout.connect(self.check_notifications)
        self.watch_notification_files()
        self.check_notifications()
        self.refresh()
        self.reposition()

    def start_worker(self, name, work):
        if self.stopping:
            return
        self._workers = [thread for thread in self._workers if thread.is_alive()]
        thread = threading.Thread(target=work, daemon=True, name=name)
        self._workers.append(thread)
        thread.start()

    def stop(self, callback):
        if self.stopping:
            return
        self.provider.stop_new_work()
        self.stopping = True
        self._stopped_callback = callback
        for timer in (self.stack_timer, self.geometry_timer, self.buttons_timer,
                      self.shell_timer, self.provider_timer, self.notification_timer,
                      self.notification_debounce, self.widget.minute_timer):
            timer.stop()
        files = self.notification_files.files()
        directories = self.notification_files.directories()
        if files:
            self.notification_files.removePaths(files)
        if directories:
            self.notification_files.removePaths(directories)
        self.events.close()
        self._stop_timer.start()
        self._finish_stop()

    def _finish_stop(self):
        self._workers = [thread for thread in self._workers if thread.is_alive()]
        if self._workers:
            return
        self._stop_timer.stop()
        try:
            self.provider.close()
        except Exception:
            logging.exception("Provider cleanup failed")
        callback, self._stopped_callback = self._stopped_callback, None
        if callback:
            callback()

    def check_notifications(self):
        if self.stopping or self.notification_busy:
            return
        self.notification_busy = True
        def work():
            try:
                self.notification_ready.emit(self.notification_watcher.check(), None)
            except Exception as error:
                self.notification_ready.emit(False, type(error).__name__)
        self.start_worker("codex-notification", work)

    def watch_notification_files(self):
        path = self.notification_watcher.path
        watched = set(self.notification_files.files() + self.notification_files.directories())
        for candidate in (path.parent, path, path.with_name(path.name + "-wal")):
            if candidate.exists() and str(candidate) not in watched:
                self.notification_files.addPath(str(candidate))

    def schedule_notification_check(self, _path):
        if self.stopping:
            return
        self.watch_notification_files()  # SQLite can recreate its WAL file.
        self.notification_debounce.start(80)

    def receive_notification(self, is_new, error):
        if self.stopping:
            return
        self.notification_busy = False
        if error:
            if not self.notification_error_reported:
                logging.warning("Codex notification watch unavailable: %s", error)
                self.notification_error_reported = True
        else:
            self.notification_error_reported = False
            if is_new and self.config.show_notification_pulse:
                self.widget.pulse_logo()

    def apply_config(self, config):
        if self.stopping:
            return
        self.config = config
        self.widget.config = config
        self.widget.update_accessibility()
        if not config.show_notification_pulse:
            self.widget.stop_logo_pulse()
        self.widget.refresh_countdown()
        self.reposition()
        self.config_changed.emit(config)

    def schedule_stacking(self):
        if self.stopping:
            return
        if not self.stack_timer.isActive():
            self.stack_timer.start(0)

    def schedule_geometry(self):
        if self.stopping:
            return
        if not self.geometry_timer.isActive():
            self.geometry_timer.start(60)

    def schedule_bounds(self):
        if self.stopping:
            return
        if not self.buttons_timer.isActive():
            self.buttons_timer.start(120)

    def refresh_bounds(self):
        if self.stopping:
            return
        if self.taskbar:
            self.scan_bounds(self.taskbar)

    def ensure_stacking(self):
        if self.stopping:
            return
        if not self.widget.isVisible() or not self.taskbar:
            return
        hwnd = int(self.widget.winId())
        if not is_own_window(hwnd):
            self.reposition()
            return
        if get_parent(hwnd) != self.taskbar.hwnd:
            self.reposition()

    def refresh(self):
        if self.stopping or self.provider_busy:
            return
        self.provider_busy = True
        def work():
            try:
                self.data_ready.emit(self.provider.get_state(), None)
            except Exception as error:
                self.data_ready.emit(None, type(error).__name__)
        self.start_worker("limit-provider", work)

    def receive_data(self, state, error):
        if self.stopping:
            return
        self.provider_busy = False
        if error:
            logging.warning("Provider refresh failed: %s", error)
            self.widget.error = True
            self.widget.refresh_countdown()
        else:
            self.widget.set_state(state)

    def cycle(self):
        if self.stopping:
            return
        if hasattr(self.provider, "cycle"):
            self.provider.cycle()
            self.refresh()

    def scan_bounds(self, taskbar):
        if self.stopping or self.bounds_busy:
            return
        self.bounds_busy = True
        self.next_bounds = time.monotonic() + 15
        def work():
            try:
                result = button_bounds(taskbar.hwnd)
            except Exception as error:
                logging.warning("Taskbar discovery failed: %s", type(error).__name__)
                result = None
            self.bounds_ready.emit(taskbar, result)
        self.start_worker("taskbar-discovery", work)

    def receive_bounds(self, taskbar, bounds):
        if self.stopping:
            return
        self.bounds_busy = False
        if taskbar == self.taskbar and bounds:
            # A transient empty UIA snapshot must not hide an already placed window.
            occupied = [(l, r) for l, t, r, b in bounds if b > taskbar.top and t < taskbar.bottom]
            if occupied:
                self.occupied = occupied
        self.reposition()

    def reposition(self):
        if self.stopping:
            return
        taskbar = discover()
        if taskbar != self.taskbar:
            self.taskbar, self.occupied = taskbar, None
            self.taskbar_window = None
            self.events.taskbar_hwnd = taskbar.hwnd if taskbar else 0
            self.next_bounds = 0
        if not taskbar:
            self.widget.hide()
            return
        if not is_own_window(int(self.widget.winId())):
            # Recover if Explorer invalidated the native child window.
            self.widget.destroy()
            self.widget.create()
            apply_overlay_style(int(self.widget.winId()))
            self.widget.placement = None
        if time.monotonic() >= self.next_bounds:
            self.scan_bounds(taskbar)
        if self.occupied is None and self.config.safe_right_x is None:
            self.widget.hide()  # Never guess whether shell controls are underneath.
            return
        taskbar_height = taskbar.bottom - taskbar.top
        desired_width = min(self.config.width, 240 if self.config.compact_view else 600)
        slot = free_slot(taskbar, self.occupied or [], self.config.offset_x, desired_width,
                         self.config.safe_right_x, self.widget.minimum_width(taskbar_height))
        if not slot:
            self.widget.hide()
            return
        x, width = slot
        height = taskbar.bottom - taskbar.top
        y = taskbar.top
        placement = (x, y, width, height, taskbar.scale, taskbar.monitor)
        changed = self.widget.placement != placement
        self.widget.placement = placement
        hwnd = int(self.widget.winId())
        attached = get_parent(hwnd) == taskbar.hwnd
        if not attached:
            self.taskbar_window = QWindow.fromWinId(taskbar.hwnd)
            self.widget.windowHandle().setParent(self.taskbar_window)
        if changed or not self.widget.isVisible() or not attached:
            place_on_taskbar(hwnd, taskbar, x, y, width, height)
        if not self.widget.isVisible():
            # Qt may restore its pre-show size on first exposure. Reapply the
            # measured physical rectangle in the same event turn, before painting.
            self.widget.show()
            place_on_taskbar(hwnd, taskbar, x, y, width, height)
        # Keep the translucent backing surface fresh after shell changes.
        QTimer.singleShot(0, self.widget.repaint)
