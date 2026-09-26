"""Small, custom-painted surfaces; no stock Qt controls or render loop."""
from ctypes import wintypes
from functools import lru_cache
from math import pi, sin
from pathlib import Path
from base64 import b64decode
from xml.etree import ElementTree
from PySide6.QtCore import Qt, QRectF, QPointF, QVariantAnimation, QEasingCurve, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QFontDatabase, QFontMetricsF, QImage, QLinearGradient, QRadialGradient
from PySide6.QtWidgets import QWidget
from models import severity
from time_helpers import format_reset_display, local_now
from windows.taskbar import apply_overlay_style
from paths import APP_NAME
from settings import NOTIFICATION_COLORS
from i18n import tr

TEXT = QColor("#f7fbff")
MUTED = QColor("#dbe6f2")


@lru_cache(maxsize=72)
def font(size=11, medium=False, font_scale=100):
    families = QFontDatabase.families()
    family = next((name for name in ("Segoe UI Variable", "Inter", "Segoe UI") if name in families), "Segoe UI")
    result = QFont(family)
    result.setPixelSize(round(size * font_scale / 100))
    result.setWeight(QFont.Weight.DemiBold if medium else QFont.Weight.Normal)
    return result


def text(painter, rect, value, color=TEXT, size=11, medium=False,
         align=Qt.AlignmentFlag.AlignLeft, font_scale=100):
    painter.setFont(font(size, medium, font_scale))
    painter.setPen(color)
    painter.drawText(QRectF(*rect), align | Qt.AlignmentFlag.AlignVCenter, value)


def countdown_width(caption, font_scale=100):
    prefix = caption_prefix(caption)
    return (QFontMetricsF(font(11, font_scale=font_scale)).horizontalAdvance(prefix)
            + QFontMetricsF(font(15, font_scale=font_scale)).horizontalAdvance(caption[len(prefix):]))


def countdown_text(painter, x, y, height, caption, font_scale=100):
    prefix = caption_prefix(caption)
    prefix_width = QFontMetricsF(font(11, font_scale=font_scale)).horizontalAdvance(prefix)
    if prefix:
        text(painter, (x, y, prefix_width + 1, height), prefix, MUTED, 11, font_scale=font_scale)
    text(painter, (x + prefix_width, y, countdown_width(caption, font_scale) - prefix_width + 1, height),
         caption[len(prefix):], MUTED, 15, font_scale=font_scale)


def caption_prefix(caption):
    return next((prefix for prefix in ("Reset: ", "Resets in ", "Resets at ", "Resets: ", "Kalan ", "Sıfırlanır ")
                 if caption.startswith(prefix)), "")


def short_caption(caption):
    if caption.startswith("Reset: "):
        return caption
    return caption[len(caption_prefix(caption)):]


def reset_caption(reset_at, now, mode, display, clock_format, compact=False, language="en"):
    if not reset_at:
        return ("Sıfırlanır —" if language == "tr" else "Resets at —") if display == "at" else "Reset: —"
    return format_reset_display(reset_at, now, mode, display, clock_format, compact, language)


def bar(painter, x, y, width, percent, height=4):
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(255, 255, 255, 68))
    painter.drawRoundedRect(QRectF(x, y, width, height), height / 2, height / 2)
    if percent > 0:
        color = QColor(severity(percent))
        fill_width = min(width, max(height, width * percent / 100))
        painter.setBrush(color)
        painter.drawRoundedRect(QRectF(x, y, fill_width, height), height / 2, height / 2)
        painter.setBrush(QColor(255, 255, 255, 34))
        painter.drawRoundedRect(QRectF(x + 1, y + .5, max(0, fill_width - 2), 1), .5, .5)


def draw_mock_badge(painter, badge, label, badge_font):
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(35, 25, 12, 235))
    painter.drawRoundedRect(badge, 3, 3)
    painter.setFont(badge_font)
    painter.setPen(QColor("#ffbd63"))
    painter.drawText(badge, Qt.AlignmentFlag.AlignCenter, label)


@lru_cache(maxsize=1)
def logo_image():
    """Render the supplied Codex silhouette in monochrome white."""
    root = ElementTree.parse(Path(__file__).parent / "assets" / "codex-icon.svg").getroot()
    image_node = root.find(".//{http://www.w3.org/2000/svg}image")
    if image_node is None:
        raise ValueError("codex-icon.svg has no embedded image")
    href = image_node.get("{http://www.w3.org/1999/xlink}href", "")
    if not href.startswith("data:image/png;base64,"):
        raise ValueError("codex-icon.svg has an unsupported embedded image")
    image = QImage.fromData(b64decode(href.split(",", 1)[1]), "PNG")
    if image.isNull():
        raise ValueError("Could not decode codex-icon.svg image")
    white = image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    painter = QPainter(white)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(white.rect(), QColor("#ffffff"))
    painter.end()
    return white


def codex_glyph(painter, x, y, glow=0., glow_color="amber"):
    image = logo_image()
    target = QRectF(x, y, 23, 23)
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
    if glow > 0:
        accent = QColor(NOTIFICATION_COLORS[glow_color][1])
        center = QPointF(x + 11.5, y + 11.5)
        radius = 16 + 13 * glow
        halo = QRadialGradient(center, radius)
        halo.setColorAt(0, QColor(accent.red(), accent.green(), accent.blue(), round(215 * glow)))
        halo.setColorAt(.55, QColor(accent.red(), accent.green(), accent.blue(), round(135 * glow)))
        halo.setColorAt(1, QColor(accent.red(), accent.green(), accent.blue(), 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(halo)
        painter.drawEllipse(center, radius, radius)
    painter.drawImage(target, image)
    painter.restore()


def notification_glow(phase):
    """Grow and fade the amber halo around the logo."""
    if phase < .30:
        return sin(phase / .30 * pi / 2)
    if phase >= .88:
        return 0.
    return (1 - (phase - .30) / .58) ** 1.1


def strip_layout(width, state, show_countdown=True, now=None, reset_display="in", clock_format=24,
                 language="en", font_scale=100):
    """Keep normal-view values on one row, shortening or hiding bars as space runs out."""
    now = now or local_now()
    label_widths = [QFontMetricsF(font(12, True, font_scale)).horizontalAdvance(label)
                    for label in (tr("five_short", language), tr("week_short", language))]
    percent_width = QFontMetricsF(font(15, True, font_scale)).horizontalAdvance("100%") + 1
    measure = lambda caption: countdown_width(caption, font_scale)

    def captions(compact):
        if not show_countdown:
            return ["", ""]
        if not state:
            empty = reset_caption(None, now, "five_hour", reset_display, clock_format, language=language)
            return [empty, empty]
        return [reset_caption(state.five_hour_reset_at, now, "five_hour", reset_display, clock_format,
                              compact=reset_display == "at", language=language),
                reset_caption(state.weekly_reset_at, now, "weekly", reset_display, clock_format,
                              compact=compact or reset_display == "at", language=language)]

    countdowns = captions(False)
    gap, between, start, right = 9, 24, 62, 14
    def fixed():
        return start + right + between + sum(label_widths) + 2 * percent_width + sum(measure(c) for c in countdowns) + (6 if show_countdown else 4) * gap
    if fixed() + 180 > width:
        countdowns = captions(True)
    bar_width = min(130, (width - fixed()) / 2)
    if bar_width < 48:
        gap, between = 5, 18
        bar_width = min(130, (width - fixed()) / 2)
    show_bars = bar_width >= 24
    if not show_bars:
        bar_width = 0
    blocks = []
    x = start
    for index in range(2):
        block = {"label": (x, label_widths[index]), "caption": countdowns[index]}
        x += label_widths[index] + gap
        block["percent"] = (x, percent_width)
        x += percent_width + gap
        if show_bars:
            block["bar"] = (x, bar_width)
            x += bar_width
        if show_countdown:
            if show_bars:
                x += gap
            block["countdown"] = (x, measure(countdowns[index]) + .5)
            x += measure(countdowns[index])
        blocks.append(block)
        if index == 0:
            divider = x + between / 2
            x += between
    return blocks, divider, x <= width - right + 1


def date_strip_layout(width, height, state, now, clock_format, language, font_scale=100):
    """Keep both dated reset values and their bars on one normal-view row."""
    labels = (tr("five_short", language), tr("week_short", language))
    dates = (state.five_hour_reset_at, state.weekly_reset_at) if state else (None, None)
    captions = [short_caption(reset_caption(date, now, mode, "at", clock_format, True, language))
                for date, mode in zip(dates, ("five_hour", "weekly"))]
    label_widths = [QFontMetricsF(font(12, True, font_scale)).horizontalAdvance(label) + 1 for label in labels]
    percent_width = QFontMetricsF(font(15, True, font_scale)).horizontalAdvance("100%") + 1
    caption_widths = [QFontMetricsF(font(11, font_scale=font_scale)).horizontalAdvance(caption) + 1
                      for caption in captions]
    start, right, gap, between = 49, 12, 5, 18
    fixed = start + right + between + sum(label_widths) + 2 * percent_width + sum(caption_widths) + 6 * gap
    bar_width = min(130, max(0, (width - fixed) / 2))
    show_bars = bar_width >= 24
    if not show_bars:
        bar_width = 0
    blocks = []
    x = start
    for index in range(2):
        block = {"index": index, "label": (x, label_widths[index]), "caption": captions[index],
                 "row": (0, height), "short": True, "logo": True}
        x += label_widths[index] + gap
        block["percent"] = (x, percent_width)
        x += percent_width + gap
        if show_bars:
            block["bar"] = (x, bar_width)
            x += bar_width + gap
        block["countdown"] = (x, caption_widths[index])
        x += caption_widths[index]
        blocks.append(block)
        if index == 0:
            divider = x + between / 2
            x += between
    return blocks, divider, x <= width - right + 1, False


def weekly_only(state):
    return state is not None and state.five_hour_percent is None and state.weekly_percent is not None


def visible_indices(state, show_five_hour=True, show_weekly=True):
    if show_five_hour and show_weekly and weekly_only(state):
        return (1,)
    return tuple(index for index, enabled in enumerate((show_five_hour, show_weekly)) if enabled)


def compact_layout(width, height, state, show_countdown, now, reset_display, clock_format,
                   language, indices, font_scale=100):
    """Two short rows with percentages and optional reset values, without bars."""
    now = now or local_now()
    row_height = height / len(indices)
    blocks = []
    for row, index in enumerate(indices):
        label = (tr("five_short", language), tr("week_short", language))[index]
        date = (state.five_hour_reset_at if index == 0 else state.weekly_reset_at) if state else None
        caption = reset_caption(date, now, "five_hour" if index == 0 else "weekly",
                                reset_display, clock_format, True, language) if show_countdown else ""
        x = 46
        label_width = QFontMetricsF(font(12, True, font_scale)).horizontalAdvance(label) + 1
        block = {"index": index, "label": (x, label_width), "caption": caption,
                 "row": (row * row_height, row_height), "short": True, "logo": True}
        x += label_width + 4
        percent_width = QFontMetricsF(font(15, True, font_scale)).horizontalAdvance("100%") + 1
        block["percent"] = (x, percent_width)
        x += percent_width + 5
        if show_countdown:
            duration = short_caption(caption)
            block["countdown"] = (x, QFontMetricsF(font(11, font_scale=font_scale)).horizontalAdvance(duration) + 1)
            x += block["countdown"][1]
        blocks.append(block)
        if x > width - 8:
            return blocks, None, False, len(indices) == 2
    return blocks, None, True, len(indices) == 2


def responsive_layout(width, height, state, show_countdown=True, now=None,
                      reset_display="in", clock_format=24, compact_view=False,
                      language="en", show_five_hour=True, show_weekly=True, font_scale=100):
    """Use two rows only in compact view; normal view always stays on one row."""
    indices = visible_indices(state, show_five_hour, show_weekly)
    if compact_view:
        return compact_layout(width, height, state, show_countdown, now, reset_display, clock_format,
                              language, indices, font_scale)
    if reset_display == "at" and show_countdown and len(indices) == 2:
        return date_strip_layout(width, height, state, now or local_now(), clock_format, language, font_scale)
    if len(indices) == 1:
        now = now or local_now()
        index = indices[0]
        date = (state.five_hour_reset_at if index == 0 else state.weekly_reset_at) if state else None
        mode = "five_hour" if index == 0 else "weekly"
        caption = reset_caption(date, now, mode, reset_display, clock_format, True, language) if show_countdown else ""
        label_width = QFontMetricsF(font(12, True, font_scale)).horizontalAdvance(
            (tr("five_short", language), tr("week_short", language))[index]) + 1
        percent_width = QFontMetricsF(font(15, True, font_scale)).horizontalAdvance("100%") + 1
        if height >= 38:
            x, gap = 62, 9
            block = {"index": index, "label": (x, label_width), "caption": caption, "row": (0, height)}
            x += label_width + gap
            block["percent"] = (x, percent_width)
            x += percent_width + gap
            remaining = countdown_width(caption, font_scale) if show_countdown else 0
            bar_width = min(130, width - x - (gap + remaining if show_countdown else 0) - 14)
            if bar_width >= 24:
                block["bar"] = (x, bar_width)
                x += bar_width
                if show_countdown:
                    block["countdown"] = (x + gap, remaining + 1)
                return [block], None, True, False
        x = 49 if height >= 38 else 5
        gap = 5
        block = {"index": index, "label": (x, label_width), "caption": caption,
                 "row": (0, height), "short": True, "logo": height >= 38}
        x += label_width + gap
        block["percent"] = (x, percent_width)
        x += percent_width + gap
        if show_countdown:
            duration = short_caption(caption)
            size = 11 if reset_display == "at" else 15
            block["countdown"] = (x, QFontMetricsF(font(size, font_scale=font_scale)).horizontalAdvance(duration) + 1)
            x += block["countdown"][1]
        return [block], None, x <= width - 5, False
    blocks, divider, fits = strip_layout(width, state, show_countdown, now, reset_display, clock_format,
                                         language, font_scale)
    for block in blocks:
        block["row"] = (0, height)
    return blocks, divider, fits, False


class Overlay(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        apply_overlay_style(int(self.winId()))

    def nativeEvent(self, kind, message):
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == 0x21:  # WM_MOUSEACTIVATE: handle mouse, preserve foreground.
            return True, 3  # MA_NOACTIVATE
        return super().nativeEvent(kind, message)


class LimitWidget(Overlay):
    cycle_requested = Signal()
    layout_changed = Signal()
    launch_requested = Signal()

    def __init__(self, config, is_mock=True, test_mode=False):
        super().__init__()
        self.config, self.is_mock, self.test_mode = config, is_mock, test_mode
        self.state = None
        self.error = False
        self.values = (0., 0.)
        self.hover = 0.
        self.logo_glow = 0.
        self.notification_active = False
        self.placement = None
        self.setWindowTitle(APP_NAME)
        self.setAccessibleName(APP_NAME)
        self.setWindowOpacity(1)
        self.resize(config.width, 40)
        self.setMouseTracking(True)
        self.hover_animation = QVariantAnimation(self)
        self.hover_animation.setDuration(170)
        self.hover_animation.valueChanged.connect(self._hover_changed)
        self.progress_animation = QVariantAnimation(self)
        self.progress_animation.setDuration(260)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.progress_animation.valueChanged.connect(self._progress_changed)
        self.logo_animation = QVariantAnimation(self)
        self.logo_animation.setDuration(3_000)
        self.logo_animation.setStartValue(0.)
        self.logo_animation.setEndValue(1.)
        self.logo_animation.setLoopCount(-1)
        self.logo_animation.valueChanged.connect(self._logo_glow_changed)
        self.minute_timer = QTimer(self)
        self.minute_timer.setInterval(60_000)
        self.minute_timer.timeout.connect(self.refresh_countdown)
        self.minute_timer.start()

    def refresh_countdown(self):
        self.layout_changed.emit()
        if self.isVisible():
            self.update()

    def _hover_changed(self, value):
        self.hover = value
        self.update()

    def _progress_changed(self, value):
        self.values = tuple(a + (b - a) * value for a, b in zip(self._from, self._to))
        self.update()

    def _logo_glow_changed(self, value):
        self.logo_glow = notification_glow(float(value))
        self.update(0, 0, 60, self.height())

    def pulse_logo(self):
        self.notification_active = True
        if not self.isVisible():
            return
        if self.logo_animation.state() == QVariantAnimation.State.Paused:
            self.logo_animation.resume()
        elif self.logo_animation.state() != QVariantAnimation.State.Running:
            self.logo_animation.start()

    def stop_logo_pulse(self):
        self.notification_active = False
        self.logo_animation.stop()
        self.logo_glow = 0.
        self.update(0, 0, 60, self.height())

    def set_state(self, state):
        self.error = False
        old = self.state
        self.state = state
        targets = (state.five_hour_percent or 0., state.weekly_percent or 0.)
        self.update_accessibility()
        if old is None or not self.isVisible():
            self.values = targets
        elif targets != (old.five_hour_percent or 0., old.weekly_percent or 0.):
            self.progress_animation.stop()
            self._from, self._to = self.values, targets
            self.progress_animation.setStartValue(0.)
            self.progress_animation.setEndValue(1.)
            self.progress_animation.start()
        self.refresh_countdown()

    def update_accessibility(self):
        if not self.state:
            return
        language = self.config.language
        parts = []
        for index in visible_indices(self.state, self.config.show_five_hour, self.config.show_weekly):
            percent = (self.state.five_hour_percent, self.state.weekly_percent)[index]
            value = (f"%{percent:g} kalan" if language == "tr" else f"{percent:g} percent remaining") if percent is not None else tr("unavailable", language)
            parts.append(f"{tr(('five', 'week')[index], language)}: {value}")
        self.setAccessibleDescription(". ".join(parts) + ".")

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        glass = QLinearGradient(0, 0, 0, h)
        alpha = self.config.opacity
        glass.setColorAt(0, QColor(20, 20, 20, round((35 + 5 * self.hover) * alpha)))
        glass.setColorAt(.48, QColor(20, 20, 20, round((30 + 5 * self.hover) * alpha)))
        glass.setColorAt(1, QColor(20, 20, 20, round((35 + 5 * self.hover) * alpha)))
        p.fillRect(self.rect(), glass)
        fade_start = max(0, w - 52)
        edge = QLinearGradient(fade_start, 0, w, 0)
        edge.setColorAt(0, QColor(0, 0, 0, 255))
        edge.setColorAt(1, QColor(0, 0, 0, 0))
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_DestinationIn)
        p.fillRect(QRectF(fade_start, 0, w - fade_start, h), edge)
        p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        blocks, divider, fits, stacked = responsive_layout(
            w, h, self.state, self.config.show_countdown, reset_display=self.config.reset_display,
            clock_format=self.config.clock_format, compact_view=self.config.compact_view,
            language=self.config.language, show_five_hour=self.config.show_five_hour,
            show_weekly=self.config.show_weekly, font_scale=self.config.font_scale)
        short = blocks[0].get("short", False)
        if not short or blocks[0].get("logo"):
            codex_glyph(p, 12, (h - 23) / 2, self.logo_glow, self.config.notification_color)
        p.setPen(QPen(QColor(255, 255, 255, 32), 1))
        if not short or blocks[0].get("logo"):
            p.drawLine(43, 5, 43, h - 5)
        if stacked:
            p.drawLine(49, round(h / 2), w - 9, round(h / 2))
        elif divider is not None:
            p.drawLine(round(divider), 7, round(divider), h - 7)
        badge = None
        if self.is_mock:
            mock_label = tr("mock", self.config.language)
            badge_font = font(9, True, self.config.font_scale)
            badge_width = QFontMetricsF(badge_font).horizontalAdvance(mock_label) + 12
            badge = QRectF(max(46, w - badge_width - 6), h - 15, badge_width, 13)
            p.save()
            p.setClipRect(QRectF(0, 0, badge.x() - 3, h))
        for position, block in enumerate(blocks):
            i = block.get("index", position)
            label = (tr("five_short", self.config.language), tr("week_short", self.config.language))[i]
            row_y, row_h = block["row"]
            x, width = block["label"]
            text(p, (x, row_y, width + 1, row_h), label, QColor("#e9f5ff"), 12, True,
                 font_scale=self.config.font_scale)
            percent = (self.state.five_hour_percent if i == 0 else self.state.weekly_percent) if self.state else None
            x, width = block["percent"]
            text(p, (x, row_y, width, row_h), f"{percent:.0f}%" if percent is not None else "—", TEXT, 15, True,
                 font_scale=self.config.font_scale)
            if "bar" in block:
                x, width = block["bar"]
                bar(p, x, row_y + row_h / 2 - 2, width, self.values[i])
            if "countdown" in block:
                x, width = block["countdown"]
                if short:
                    text(p, (x, row_y, width, row_h), short_caption(block["caption"]), MUTED,
                         11 if self.config.compact_view or self.config.reset_display == "at" or stacked else 15,
                         font_scale=self.config.font_scale)
                else:
                    countdown_text(p, x, row_y, row_h, block["caption"], self.config.font_scale)
        if badge is not None:
            p.restore()
            draw_mock_badge(p, badge, mock_label, badge_font)
        if self.error:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#cbb387"))
            p.drawEllipse(QRectF(w - 6, 4, 3, 3))

    def minimum_width(self, height=48):
        if self.config.compact_view:
            return 240  # Compact content intentionally clips at the right edge.
        # Fonts stay legible; never draw overlapping labels in an impossible slot.
        for width in range(240, 1001, 4):
            if responsive_layout(width, height, self.state, self.config.show_countdown,
                                 reset_display=self.config.reset_display,
                                 clock_format=self.config.clock_format,
                                 compact_view=self.config.compact_view,
                                 language=self.config.language,
                                 show_five_hour=self.config.show_five_hour,
                                 show_weekly=self.config.show_weekly,
                                 font_scale=self.config.font_scale)[2]:
                return width
        return 1000

    def animate_hover(self, target):
        self.hover_animation.stop()
        self.hover_animation.setStartValue(self.hover)
        self.hover_animation.setEndValue(target)
        self.hover_animation.start()

    def enterEvent(self, event):
        self.animate_hover(1.)

    def leaveEvent(self, event):
        self.animate_hover(0.)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.height() >= 38 and event.position().x() < 43:
            self.stop_logo_pulse()
            self.launch_requested.emit()
            return
        if event.button() == Qt.MouseButton.RightButton and self.test_mode:
            self.cycle_requested.emit()

    def showEvent(self, event):
        super().showEvent(event)
        if self.notification_active:
            if self.logo_animation.state() == QVariantAnimation.State.Paused:
                self.logo_animation.resume()
            elif self.logo_animation.state() == QVariantAnimation.State.Stopped:
                self.logo_animation.start()

    def hideEvent(self, event):
        self.progress_animation.stop()
        if self.logo_animation.state() == QVariantAnimation.State.Running:
            self.logo_animation.pause()
        if self.state:
            self.values = (self.state.five_hour_percent or 0., self.state.weekly_percent or 0.)
        super().hideEvent(event)
