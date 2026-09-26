"""Out-of-process WinEvents delivered by the existing Qt message loop.

No DLL, injection, Explorer patching, or foreground activation.
"""
import ctypes as C
from ctypes import wintypes as W
from PySide6.QtCore import QObject, Signal, QAbstractNativeEventFilter
from PySide6.QtWidgets import QApplication
from windows.taskbar import bind, get_ancestor, get_foreground, find_window

CALLBACK = C.WINFUNCTYPE(None, W.HANDLE, W.DWORD, W.HWND, W.LONG, W.LONG, W.DWORD, W.DWORD)
set_hook = bind("SetWinEventHook", W.HANDLE, W.DWORD, W.DWORD, W.HMODULE, CALLBACK, W.DWORD, W.DWORD, W.DWORD)
unhook = bind("UnhookWinEvent", W.BOOL, W.HANDLE)
register_message = bind("RegisterWindowMessageW", W.UINT, W.LPCWSTR)


class ShellMessages(QAbstractNativeEventFilter):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.taskbar_created = register_message("TaskbarCreated")

    def nativeEventFilter(self, event_type, message):
        msg = W.MSG.from_address(int(message))
        if msg.message in (self.taskbar_created, 0x7E, 0x1A):
            self.owner.geometry_changed.emit()
        elif msg.message == 0x1E:  # WM_TIMECHANGE
            self.owner.clock_changed.emit()
        return False, 0


class ShellEvents(QObject):
    stacking_changed = Signal()
    geometry_changed = Signal()
    buttons_changed = Signal()
    clock_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.taskbar_hwnd = find_window("Shell_TrayWnd", None)
        self.last_non_taskbar_foreground = 0
        self._remember_foreground(get_foreground())
        self._callback = CALLBACK(self._event)
        self.handles = []
        self._closed = False
        self.filter = ShellMessages(self)
        QApplication.instance().installNativeEventFilter(self.filter)
        # Register only the event families we need; skip our own repaint/position events.
        try:
            for first, last in ((3, 3), (0x14, 0x17), (0x8000, 0x8004), (0x800B, 0x800B)):
                handle = set_hook(first, last, None, self._callback, 0, 0, 0x2)
                if not handle:
                    raise C.WinError(C.get_last_error())
                self.handles.append(handle)
        except Exception:
            self.close()
            raise
        QApplication.instance().aboutToQuit.connect(self.close)

    def _event(self, hook, event, hwnd, object_id, child, thread, timestamp):
        if event < 0x8000:
            if event == 3:  # EVENT_SYSTEM_FOREGROUND
                self._remember_foreground(hwnd)
            self.stacking_changed.emit()
            return
        if not hwnd:
            return
        root = get_ancestor(hwnd, 2)
        is_shell = hwnd == self.taskbar_hwnd or root == self.taskbar_hwnd
        if is_shell:
            if event in (0x8000, 0x8001, 0x8002, 0x8003, 0x800B):
                self.geometry_changed.emit() if hwnd == self.taskbar_hwnd and object_id == 0 else self.buttons_changed.emit()
            if event in (0x8002, 0x8004, 0x800B):
                self.stacking_changed.emit()
        elif event == 0x8004 or (event in (0x8002, 0x800B) and object_id == 0):
            # Z-order changes can be reported on the desktop parent, not the taskbar.
            self.stacking_changed.emit()

    def _remember_foreground(self, hwnd):
        root = get_ancestor(hwnd, 2) if hwnd else 0
        if root and root != self.taskbar_hwnd:
            self.last_non_taskbar_foreground = int(root)

    def close(self):
        if self._closed:
            return
        self._closed = True
        for handle in self.handles:
            unhook(handle)
        self.handles.clear()
        QApplication.instance().removeNativeEventFilter(self.filter)
