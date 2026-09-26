"""Find, activate, or launch the installed Codex desktop window."""
import ctypes as C
from ctypes import wintypes as W
import logging
import os
import subprocess
import threading
import time

from windows.taskbar import bind, get_ancestor, get_foreground, get_rect, get_style, is_visible

kernel32 = C.WinDLL("kernel32", use_last_error=True)
enum_windows = bind("EnumWindows", W.BOOL, C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM), W.LPARAM)
get_pid = bind("GetWindowThreadProcessId", W.DWORD, W.HWND, C.POINTER(W.DWORD))
get_owner = bind("GetWindow", W.HWND, W.HWND, W.UINT)
get_title = bind("GetWindowTextW", C.c_int, W.HWND, W.LPWSTR, C.c_int)
is_iconic = bind("IsIconic", W.BOOL, W.HWND)
show_window = bind("ShowWindow", W.BOOL, W.HWND, C.c_int)
set_foreground = bind("SetForegroundWindow", W.BOOL, W.HWND)
bring_to_top = bind("BringWindowToTop", W.BOOL, W.HWND)
attach_input = bind("AttachThreadInput", W.BOOL, W.DWORD, W.DWORD, W.BOOL)
current_thread = kernel32.GetCurrentThreadId
current_thread.restype = W.DWORD
open_process = kernel32.OpenProcess
open_process.argtypes = (W.DWORD, W.BOOL, W.DWORD)
open_process.restype = W.HANDLE
query_image = kernel32.QueryFullProcessImageNameW
query_image.argtypes = (W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD))
query_image.restype = W.BOOL
close_handle = kernel32.CloseHandle
close_handle.argtypes = (W.HANDLE,)
close_handle.restype = W.BOOL
_launch_lock = threading.Lock()
_last_launch = 0.


def _process_path(pid):
    handle = open_process(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return ""
    try:
        buffer, length = C.create_unicode_buffer(32768), W.DWORD(32768)
        return buffer.value.lower() if query_image(handle, 0, buffer, C.byref(length)) else ""
    finally:
        close_handle(handle)


def find_codex_window(preferred_hwnd=0):
    """Choose a visible unowned main window from the Codex desktop package."""
    candidates = []
    callback_type = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)

    def visit(hwnd, _):
        if not is_visible(hwnd) or get_owner(hwnd, 4) or get_style(hwnd, -20) & 0x80:
            return True
        pid = W.DWORD()
        get_pid(hwnd, C.byref(pid))
        path = _process_path(pid.value)
        if "\\openai.codex_" not in path and "\\openai\\codex\\app\\" not in path:
            return True
        if not path.endswith(("\\chatgpt.exe", "\\codex.exe")):
            return True
        title = C.create_unicode_buffer(512)
        get_title(hwnd, title, len(title))
        score = (10 if title.value.lower() in ("codex", "chatgpt") else 0) + (2 if not is_iconic(hwnd) else 0)
        rect = W.RECT()
        area = max(0, rect.right - rect.left) * max(0, rect.bottom - rect.top) if get_rect(hwnd, C.byref(rect)) else 0
        candidates.append((score, area, int(hwnd)))
        return True

    enum_windows(callback_type(visit), 0)
    foreground = get_ancestor(get_foreground(), 2)
    for _, _, hwnd in candidates:
        if hwnd == foreground:
            return hwnd
    for _, _, hwnd in candidates:
        if hwnd == preferred_hwnd:
            return hwnd
    return max(candidates, default=(0, 0, None))[2]


def activate_codex_window(hwnd):
    if is_iconic(hwnd):
        show_window(hwnd, 9)  # SW_RESTORE
    else:
        show_window(hwnd, 5)  # SW_SHOW
    if set_foreground(hwnd):
        return True
    foreground = get_foreground()
    foreground_thread = get_pid(foreground, None) if foreground else 0
    own_thread = current_thread()
    if foreground_thread and foreground_thread != own_thread and attach_input(own_thread, foreground_thread, True):
        try:
            bring_to_top(hwnd)
            if set_foreground(hwnd):
                return True
        finally:
            attach_input(own_thread, foreground_thread, False)
    logging.debug("Windows declined Codex foreground activation")
    return False


def launch_codex():
    """Resolve the installed MSIX package rather than storing a versioned exe path."""
    command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
               "(Get-AppxPackage -Name OpenAI.Codex | Select-Object -First 1 -ExpandProperty PackageFamilyName)"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=8,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    family = result.stdout.strip()
    if result.returncode or not family.startswith("OpenAI.Codex_") or any(c.isspace() for c in family):
        raise FileNotFoundError("Codex Desktop package is not installed")
    os.startfile(f"shell:AppsFolder\\{family}!App")


def toggle_codex_window(last_non_taskbar_foreground=0, taskbar_hwnd=0):
    """Minimize the foreground Codex window, or restore, activate, or launch it."""
    # Recheck under the lock so two quick clicks never launch two instances.
    global _last_launch
    if not _launch_lock.acquire(blocking=False):
        return
    try:
        foreground = get_ancestor(get_foreground(), 2)
        effective_foreground = (last_non_taskbar_foreground
                                if not foreground or foreground == taskbar_hwnd else foreground)
        hwnd = find_codex_window(effective_foreground)
        if hwnd:
            if not is_iconic(hwnd) and effective_foreground == hwnd:
                show_window(hwnd, 6)  # SW_MINIMIZE; never close the Codex process.
            else:
                activate_codex_window(hwnd)
        elif time.monotonic() - _last_launch >= 10:
            _last_launch = time.monotonic()
            launch_codex()
    except (OSError, subprocess.SubprocessError) as error:
        logging.warning("Codex launcher failed: %s", type(error).__name__)
    finally:
        _launch_lock.release()
