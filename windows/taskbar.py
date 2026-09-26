"""Read-only shell discovery and native styles on our own HWND only."""
import ctypes as C
from ctypes import wintypes as W
from dataclasses import dataclass
import os

user32 = C.WinDLL("user32", use_last_error=True)


def bind(name, restype, *args):
    fn = getattr(user32, name)
    fn.restype, fn.argtypes = restype, args
    return fn


find_window = bind("FindWindowW", W.HWND, W.LPCWSTR, W.LPCWSTR)
get_rect = bind("GetWindowRect", W.BOOL, W.HWND, C.POINTER(W.RECT))
is_visible = bind("IsWindowVisible", W.BOOL, W.HWND)
is_window = bind("IsWindow", W.BOOL, W.HWND)
get_foreground = bind("GetForegroundWindow", W.HWND)
get_class = bind("GetClassNameW", C.c_int, W.HWND, W.LPWSTR, C.c_int)
get_style = bind("GetWindowLongPtrW", C.c_ssize_t, W.HWND, C.c_int)
set_style = bind("SetWindowLongPtrW", C.c_ssize_t, W.HWND, C.c_int, C.c_ssize_t)
set_pos = bind("SetWindowPos", W.BOOL, W.HWND, W.HWND, C.c_int, C.c_int, C.c_int, C.c_int, W.UINT)
get_dpi = bind("GetDpiForWindow", W.UINT, W.HWND)
monitor_from = bind("MonitorFromWindow", W.HMONITOR, W.HWND, W.DWORD)
get_ancestor = bind("GetAncestor", W.HWND, W.HWND, W.UINT)
get_parent = bind("GetParent", W.HWND, W.HWND)
get_window_pid = bind("GetWindowThreadProcessId", W.DWORD, W.HWND, C.POINTER(W.DWORD))


def is_own_window(hwnd: int) -> bool:
    pid = W.DWORD()
    return bool(is_window(hwnd) and get_window_pid(hwnd, C.byref(pid)) and pid.value == os.getpid())

class MonitorInfo(C.Structure):
    _fields_ = [("cbSize", W.DWORD), ("rcMonitor", W.RECT), ("rcWork", W.RECT), ("dwFlags", W.DWORD)]


monitor_info = bind("GetMonitorInfoW", W.BOOL, W.HMONITOR, C.POINTER(MonitorInfo))


@dataclass(frozen=True)
class Taskbar:
    hwnd: int
    left: int
    top: int
    right: int
    bottom: int
    scale: float
    monitor: tuple[int, int, int, int]


def discover() -> Taskbar | None:
    hwnd = find_window("Shell_TrayWnd", None)
    rect = W.RECT()
    if not hwnd or not is_visible(hwnd) or not get_rect(hwnd, C.byref(rect)):
        return None
    info = MonitorInfo(cbSize=C.sizeof(MonitorInfo))
    if not monitor_info(monitor_from(hwnd, 2), C.byref(info)):
        return None
    mon = info.rcMonitor
    # Auto-hidden and vertical taskbars have no usable horizontal slot.
    visible_height = min(rect.bottom, mon.bottom) - max(rect.top, mon.top)
    if visible_height < 24 or rect.right - rect.left < rect.bottom - rect.top:
        return None
    return Taskbar(int(hwnd), rect.left, rect.top, rect.right, rect.bottom,
                   (get_dpi(hwnd) or 96) / 96, (mon.left, mon.top, mon.right, mon.bottom))


def apply_overlay_style(hwnd: int):
    style = get_style(hwnd, -20)
    set_style(hwnd, -20, (style | 0x80 | 0x08000000) & ~0x40000)


def place(hwnd: int, x: int, y: int, width: int, height: int):
    # HWND_TOPMOST, SWP_NOACTIVATE | SWP_NOOWNERZORDER.
    if not set_pos(hwnd, -1, x, y, width, height, 0x10 | 0x200):
        raise C.WinError(C.get_last_error())


def place_on_taskbar(hwnd: int, taskbar: Taskbar, x: int, y: int, width: int, height: int):
    if not set_pos(hwnd, 0, x - taskbar.left, y - taskbar.top, width, height, 0x10 | 0x200):
        raise C.WinError(C.get_last_error())


def free_slot(taskbar: Taskbar, occupied, offset: int, desired: int, safe_right=None, minimum=240):
    """Select a free interval on the left half, in physical pixels."""
    scale = taskbar.scale
    start = taskbar.left + round(offset * scale)
    end = (taskbar.left + taskbar.right) // 2 - round(12 * scale)
    if safe_right is not None:
        end = min(end, taskbar.left + round(safe_right * scale))
    gaps = []
    for left, right in sorted(occupied):
        left, right = left - round(8 * scale), right + round(8 * scale)
        if right <= start or left >= end:
            continue
        if left > start:
            gaps.append((start, min(left, end)))
        start = max(start, right)
    if start < end:
        gaps.append((start, end))
    minimum = round(minimum * scale)
    for left, right in gaps:
        if right - left >= minimum:
            return left, min(round(desired * scale), right - left)
    return None
