import unittest
from base64 import b64decode
from dataclasses import replace
from pathlib import Path
from xml.etree import ElementTree

from PySide6.QtGui import QImage, QPainter
from PySide6.QtWidgets import QApplication

from providers.mock import MockLimitProvider
from settings import Config
import widget as widget_module
from widget import LimitWidget, responsive_layout, draw_mock_badge, codex_glyph, logo_image


class WidgetModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_compact_stays_240_and_clips_two_rows(self):
        state = MockLimitProvider().get_state()
        for language in ("en", "tr"):
            for reset_display in ("in", "at"):
                config = replace(Config(), compact_view=True, width=240, language=language,
                                 reset_display=reset_display, font_scale=115)
                widget = LimitWidget(config, is_mock=False)
                try:
                    self.assertEqual(widget.minimum_width(48), 240)
                    blocks, _, _, stacked = responsive_layout(
                        240, 48, state, compact_view=True, language=language,
                        reset_display=reset_display, font_scale=115)
                    self.assertTrue(stacked)
                    self.assertEqual([block["row"] for block in blocks], [(0, 24), (24, 24)])
                    self.assertTrue(all("bar" not in block for block in blocks))
                finally:
                    widget.minute_timer.stop()
                    widget.close()

    def test_mock_badge_is_drawn_only_for_example_data(self):
        for language, label in (("en", "MOCK DATA"), ("tr", "ÖRNEK VERİ")):
            config = replace(Config(), compact_view=True, width=240, language=language)
            images = []
            for is_mock in (False, True):
                widget = LimitWidget(config, is_mock=is_mock)
                try:
                    widget.resize(240, 48)
                    image = QImage(240, 48, QImage.Format.Format_ARGB32_Premultiplied)
                    image.fill(0)
                    labels = []
                    def capture_badge(painter, rect, text, badge_font):
                        labels.append(text)
                        draw_mock_badge(painter, rect, text, badge_font)
                    widget_module.draw_mock_badge = capture_badge
                    try:
                        widget.render(image)
                    finally:
                        widget_module.draw_mock_badge = draw_mock_badge
                    self.assertEqual(labels, [label] if is_mock else [])
                    images.append(image)
                finally:
                    widget.minute_timer.stop()
                    widget.close()
            self.assertNotEqual(images[0].pixelColor(230, 40), images[1].pixelColor(230, 40), label)

    def test_codex_icon_is_white_with_unchanged_shape_and_glow_behind(self):
        icon = logo_image()
        self.assertEqual((icon.width(), icon.height()), (36, 36))
        root = ElementTree.parse(Path(__file__).resolve().parents[1] / "assets" / "codex-icon.svg")
        embedded = root.find(".//{http://www.w3.org/2000/svg}image")
        original = QImage.fromData(b64decode(embedded.get(
            "{http://www.w3.org/1999/xlink}href").split(",", 1)[1]), "PNG")
        self.assertTrue(all(icon.pixelColor(x, y).alpha() == original.pixelColor(x, y).alpha()
                            for y in range(36) for x in range(36)))
        self.assertTrue(all(icon.pixelColor(x, y).getRgb()[:3] == (255, 255, 255)
                            for y in range(36) for x in range(36)
                            if icon.pixelColor(x, y).alpha()))
        renders = []
        for glow in (0., 1.):
            image = QImage(48, 48, QImage.Format.Format_ARGB32_Premultiplied)
            image.fill(0)
            painter = QPainter(image)
            codex_glyph(painter, 10, 10, glow)
            painter.end()
            renders.append(image)
        plain, glowing = renders
        self.assertNotEqual(plain.pixelColor(8, 21), glowing.pixelColor(8, 21))


if __name__ == "__main__":
    unittest.main()
