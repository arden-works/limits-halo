"""Separate-process windows used only by verify_zorder.py; no user windows edited."""
import ctypes
import json
import time
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QWidget

app = QApplication([])
app.setQuitOnLastWindowClosed(False)
windows = [QWidget(None, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint) for _ in range(2)]
for index, window in enumerate(windows):
    window.setWindowTitle(f"AI Limit Monitor test fixture {index + 1}")
    window.setStyleSheet("background:#23232a;")
    window.setGeometry(20, 850, 700, 224)
foreground = ctypes.WinDLL("user32").SetForegroundWindow
foreground.argtypes = [ctypes.c_void_p]
get_foreground = ctypes.WinDLL("user32").GetForegroundWindow
get_foreground.restype = ctypes.c_void_p
step = 0


def advance():
    global step
    if step == 24:
        app.quit()
        return
    window = windows[step % 2]
    other = windows[(step + 1) % 2]
    action = ("switch", "maximize", "minimize-restore", "topmost-overlap")[step % 4]
    if action == "maximize":
        window.showMaximized()
    else:
        if action == "minimize-restore":
            window.showMinimized()
        window.showNormal()
    window.raise_()
    window.activateWindow()
    foreground(int(window.winId()))
    if action == "minimize-restore":
        other.showMinimized()
    print(json.dumps({"step": step, "action": action, "hwnd": int(window.winId()), "foreground": get_foreground(), "at": time.perf_counter()}), flush=True)
    step += 1


timer = QTimer()
timer.timeout.connect(advance)
timer.start(450)
QTimer.singleShot(100, advance)
app.exec()
