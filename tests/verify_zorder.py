"""Cross-process taskbar attachment and focus regression with recovery polling disabled."""
import sys
import json
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QProcess, QTimer, QObject, QEvent
from PySide6.QtWidgets import QApplication
from settings import Config
from widget import LimitWidget
from controller import Controller
from providers.mock import MockLimitProvider
from windows.taskbar import get_foreground, get_style, get_rect, get_parent, user32, W, C

user32.WindowFromPoint.restype = W.HWND
user32.WindowFromPoint.argtypes = [W.POINT]

app = QApplication([])
app.setQuitOnLastWindowClosed(False)
widget = LimitWidget(Config())
controller = Controller(widget, MockLimitProvider(), Config())
controller.shell_timer.stop()  # The previous timer-repair implementation cannot pass.
controller.provider_timer.stop()
process = QProcess()
process.setProgram(sys.executable)
process.setArguments([str(Path(__file__).with_name("window_fixture.py"))])
checks, failures, pending = [], [], []
events = {"stack": 0, "hide": 0, "activation": 0}
started = False


class VisibilityObserver(QObject):
    def eventFilter(self, watched, event):
        if started and event.type() == QEvent.Type.Hide:
            events["hide"] += 1
        if started and event.type() == QEvent.Type.WindowActivate:
            events["activation"] += 1
        return False


observer = VisibilityObserver()
widget.installEventFilter(observer)
controller.events.stacking_changed.connect(lambda: events.__setitem__("stack", events["stack"] + 1))


def receive():
    while process.canReadLine():
        item = json.loads(bytes(process.readLine()))
        pending.append(item)


def sample():
    now = time.perf_counter()
    for item in list(pending):
        elapsed = now - item["at"]
        if elapsed < .04:
            continue
        hwnd = int(widget.winId())
        rect = W.RECT()
        get_rect(hwnd, C.byref(rect))
        is_front = user32.WindowFromPoint(W.POINT(rect.left + 100, (rect.top + rect.bottom) // 2)) == hwnd
        preserved = get_foreground() != int(widget.winId())
        attached = get_parent(hwnd) == controller.taskbar.hwnd
        if widget.isVisible() and attached and preserved:
            checks.append({"step": item["step"], "action": item["action"],
                           "verified_after_ms": round(elapsed * 1000, 1),
                           "fixture_foreground": get_foreground() == item["hwnd"],
                           "unobscured_by_fixture": is_front})
            pending.remove(item)
        elif elapsed > .25:
            failures.append({**item, "visible": widget.isVisible(), "attached": attached,
                             "foreground_preserved": preserved})
            pending.remove(item)


def start_when_ready():
    global started
    if widget.isVisible():
        started = True
        readiness.stop()
        process.start()


def finish(*args):
    sample()
    if process.exitCode():
        failures.append({"exit_code": process.exitCode(), "stderr": bytes(process.readAllStandardError()).decode(errors="replace")})
    if len(checks) != 24 or pending or events["hide"] or events["activation"] or failures:
        failures.append({"completed_checks": len(checks), "pending": len(pending), "events": events})
    result = {"pass": not failures, "checks": checks, "failures": failures, "events": events,
              "styles": hex(get_style(int(widget.winId()), -20)), "polling_disabled": True}
    out = Path(__file__).resolve().parents[1] / "artifacts" / "zorder-check.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    controller.events.close()
    app.exit(0 if result["pass"] else 1)


process.readyReadStandardOutput.connect(receive)
process.finished.connect(finish)
poll = QTimer()
poll.timeout.connect(sample)
poll.start(5)  # Test observation only; production has no sampling/render loop.
readiness = QTimer()
readiness.timeout.connect(start_when_ready)
readiness.start(25)
def timeout():
    failures.append({"error": "test timed out"})
    if process.state() != QProcess.ProcessState.NotRunning:
        process.kill()
    else:
        finish()
QTimer.singleShot(20_000, timeout)
raise SystemExit(app.exec())
