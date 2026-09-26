"""Production render checks and deterministic shell lifecycle regressions."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QImage, QPainter, QColor
from PySide6.QtCore import QPoint
from PySide6.QtTest import QTest
from settings import Config
from providers.mock import MockLimitProvider
from widget import LimitWidget, text, strip_layout
from windows.taskbar import get_style, get_foreground, place, Taskbar, get_rect, get_parent, discover, C, W
from controller import Controller

app = QApplication([])
out = Path(__file__).resolve().parents[1] / 'artifacts'
out.mkdir(exist_ok=True)
before = get_foreground()
widget = LimitWidget(Config())
provider = MockLimitProvider(42, 53)
provider.week_reset = datetime.now(timezone.utc) + timedelta(days=2, hours=3, minutes=17)
widget.set_state(provider.get_state())
place(int(widget.winId()), 20, 1036, 637, 40)
widget.show()
QTest.qWait(250)
assert get_foreground() == before
style = get_style(int(widget.winId()), -20)
assert style & 0x08000000 and style & 0x80 and not style & 0x40000
widget.hide()

def render(surface):
    image = QImage(surface.width() * 2, surface.height() * 2, QImage.Format.Format_ARGB32_Premultiplied)
    image.setDevicePixelRatio(2)
    image.fill(QColor(0, 0, 0, 0))
    surface.render(image)
    return image

sheet = QImage(1100, 740, QImage.Format.Format_ARGB32_Premultiplied)
sheet.fill(QColor('#121115'))
p = QPainter(sheet)
text(p, (26, 8, 1040, 40), 'AI LIMIT MONITOR / TASKBAR STRIP', QColor('#b2b2bf'), 14, True)
for index, width in enumerate((720, 637, 560, 480)):
    widget.resize(width, 40)
    blocks, divider, fits = strip_layout(width, widget.state)
    assert fits, (width, blocks)
    for block in blocks:
        assert block['bar'][1] >= 24
        assert block['countdown'][0] + block['countdown'][1] <= width - 12
    text(p, (26, 54 + index * 76, 900, 22), f'{width} PX / BOTH COUNTDOWNS', QColor('#8d8d9b'), 10)
    p.drawImage(QPoint(26, 79 + index * 76), render(widget))
widget.resize(637, 40)
assert render(widget).save(str(out / 'widget.png'))
for index, value in enumerate((5, 40, 72, 88, 97, 100)):
    provider.five_hour = provider.weekly = value
    widget.set_state(provider.get_state())
    p.drawImage(QPoint(26, 394 + index * 51), render(widget))
p.end()
assert sheet.save(str(out / 'visual-check.png'))
widget.show()
provider.five_hour = 42
widget.set_state(provider.get_state())
assert widget.progress_animation.state() == widget.progress_animation.State.Running
QTest.qWait(320)
assert abs(widget.values[0] - 42) < .01
assert get_foreground() == before

real_taskbar = discover()
assert real_taskbar is not None
taskbar = Taskbar(real_taskbar.hwnd, 0, 1032, 1920, 1080, 1, (0, 0, 1920, 1080))
with patch.object(Controller, 'refresh'), patch.object(Controller, 'scan_bounds'), patch('controller.discover', return_value=taskbar):
    controller = Controller(widget, provider, Config())
    controller.shell_timer.stop()
    controller.provider_timer.stop()
    controller.receive_bounds(taskbar, [(665, 1032, 1256, 1080)])
    assert widget.isVisible() and widget.placement[:4] == (0, 1032, 600, 48)
    actual = W.RECT()
    get_rect(int(widget.winId()), C.byref(actual))
    assert (actual.left, actual.top, actual.right - actual.left, actual.bottom - actual.top) == widget.placement[:4]
    assert get_parent(int(widget.winId())) == taskbar.hwnd
    controller.ensure_stacking()
    assert get_parent(int(widget.winId())) == taskbar.hwnd
    get_rect(int(widget.winId()), C.byref(actual))
    assert (actual.left, actual.top, actual.right - actual.left, actual.bottom - actual.top) == widget.placement[:4]
    controller.ensure_stacking()
    assert get_parent(int(widget.winId())) == taskbar.hwnd
    # Empty or failed transient accessibility responses must not flash the window.
    controller.receive_bounds(taskbar, [])
    assert widget.isVisible()
    controller.receive_bounds(taskbar, None)
    assert widget.isVisible()
    # Reposition without a geometry change must not reassert topmost periodically.
    with patch('controller.place_on_taskbar') as native_place:
        for _ in range(5):
            controller.reposition()
        native_place.assert_not_called()
    with patch('controller.discover', return_value=None):
        controller.reposition()
        assert not widget.isVisible()
    controller.reposition()
    assert not widget.isVisible()
    controller.receive_bounds(taskbar, [(520, 1032, 1256, 1080)])
    assert widget.isVisible() and widget.placement[2] == 512
    controller.receive_bounds(taskbar, [(210, 1032, 1256, 1080)])
    assert not widget.isVisible()
    controller.events.close()
widget.close()
print('PASS: native styles, foreground, animation, 4 responsive widths, thresholds, transient UIA, no polling raise, Explorer recovery, collisions')
