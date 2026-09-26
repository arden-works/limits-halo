import tempfile
import unittest
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QPoint

from settings import Config
from settings_ui import SettingsControls
from widget import font, responsive_layout
from providers.mock import MockLimitProvider
from i18n import tr


class FakeController:
    def __init__(self):
        self.config = Config()
        self.applied = []
        self.refreshed = False

    def apply_config(self, config):
        self.config = config
        self.applied.append(config)

    def refresh(self):
        self.refreshed = True


class SettingsUiTests(unittest.TestCase):
    def test_normal_widget_never_stacks_and_hides_bars_when_narrow(self):
        QApplication.instance() or QApplication([])
        state = MockLimitProvider().get_state()
        for language in ("tr", "en"):
            for font_scale in (85, 100, 115):
                for reset_display in ("in", "at"):
                    for width in (240, 320, 400, 440, 500):
                        blocks, _, fits, stacked = responsive_layout(
                            width, 48, state, reset_display=reset_display,
                            clock_format=12, language=language, font_scale=font_scale)
                        self.assertFalse(stacked)
                        self.assertEqual([block["row"] for block in blocks], [(0, 48), (0, 48)])
                        if fits:
                            self.assertTrue(all(block["countdown"][0] + block["countdown"][1]
                                                <= width for block in blocks))
        for reset_display, narrow_width in (("in", 440), ("at", 400)):
            narrow, _, fits, _ = responsive_layout(narrow_width, 48, state,
                reset_display=reset_display, clock_format=12, language="tr")
            self.assertTrue(fits)
            self.assertTrue(all("bar" not in block for block in narrow))
            wide, _, fits, _ = responsive_layout(500, 48, state,
                reset_display=reset_display, clock_format=12, language="tr")
            self.assertTrue(fits)
            self.assertTrue(all("bar" in block for block in wide))

    def test_choice_columns_align_in_both_languages(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            controls = SettingsControls(FakeController(), Path(directory) / "config.json")
            settings = controls.settings
            try:
                settings.show()
                settings.font_size.buttons[2].click()
                for language in ("tr", "en"):
                    if language == "en":
                        settings.language.buttons[1].click()
                    app.processEvents()
                    first = [settings.five, settings.language.buttons[0], settings.view.buttons[0],
                             settings.reset.buttons[0], settings.clock.buttons[0]]
                    second = [settings.week, settings.language.buttons[1], settings.view.buttons[1],
                              settings.reset.buttons[1], settings.clock.buttons[1]]
                    first += [settings.color.buttons[index] for index in (0, 2, 4, 6)]
                    second += [settings.color.buttons[index] for index in (1, 3, 5)]
                    self.assertEqual(settings.width(), 760)
                    self.assertEqual(len({button.mapTo(settings, QPoint()).x() for button in first}), 1)
                    self.assertEqual(len({button.mapTo(settings, QPoint()).x() for button in second}), 1)
                    color_rows = [settings.color.buttons[index].geometry().y() for index in (0, 2, 4, 6)]
                    self.assertEqual(color_rows, sorted(set(color_rows)))
                    for left, right in ((0, 1), (2, 3), (4, 5)):
                        self.assertEqual(settings.color.buttons[left].geometry().y(),
                                         settings.color.buttons[right].geometry().y())
                    for button in first + second:
                        self.assertLessEqual(button.sizeHint().width(), button.width(), button.text())
                    font_buttons = settings.font_size.buttons
                    self.assertEqual([button.width() for button in font_buttons], [160] * 3)
                    self.assertEqual(len({button.geometry().y() for button in font_buttons}), 1)
                    font_x = [button.mapTo(settings, QPoint()).x() for button in font_buttons]
                    self.assertEqual(font_x[1] - font_x[0], font_x[2] - font_x[1])
                    self.assertEqual(font_x[0], first[0].mapTo(settings, QPoint()).x())
                    for button in font_buttons:
                        self.assertLessEqual(button.sizeHint().width(), button.width(), button.text())
            finally:
                settings.close()

    def test_display_choices_save_and_apply(self):
        app = QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            controller = FakeController()
            controls = SettingsControls(controller, path)
            try:
                self.assertFalse(controls.settings.windowIcon().isNull())
                self.assertIn("background: #17191d", controls.settings.styleSheet().lower())
                self.assertIn("qradioButton::indicator:checked".lower(), controls.settings.styleSheet().lower())
                self.assertIn("bahnschrift", controls.settings.styleSheet().lower())
                self.assertEqual(controls.settings.color.buttons[3].property("choiceColor"), "violet")
                self.assertIn("background: #a782ff", controls.settings.styleSheet().lower())
                self.assertEqual(tr("five_short", "tr"), "5SA")
                self.assertEqual(tr("synced", "tr"), "Veriler güncel")
                self.assertEqual(tr("quit", "tr"), "Çıkış Yap")
                self.assertEqual((controls.settings.reset.buttons[0].text(),
                                  controls.settings.reset.buttons[1].text()),
                                 ("Kalan süre", "Gün / Saat"))
                controls.settings.color.buttons[3].click()
                controls.settings.reset.buttons[1].click()
                controls.settings.clock.buttons[0].click()
                controls.settings.view.buttons[1].click()
                controls.settings.font_size.buttons[2].click()
                self.assertIn("font-size: 16px", controls.settings.styleSheet())
                controls.settings.color.buttons[6].click()
                self.assertFalse(controller.config.show_notification_pulse)
                controls.settings.color.buttons[3].click()
                self.assertTrue(controller.config.show_notification_pulse)
                controls.settings.color.buttons[6].click()
                controls.settings.week.setChecked(False)
                self.assertTrue(controls.settings.five.isEnabled())
                self.assertTrue(controls.settings.five.isChecked())
                controls.settings.five.click()
                self.assertTrue(controls.settings.five.isChecked())
                controls.settings.language.buttons[1].click()
                self.assertEqual(controls.settings.windowTitle(), "LimitsHalo · Settings")
                self.assertEqual((controls.settings.reset.buttons[0].text(),
                                  controls.settings.reset.buttons[1].text()),
                                 ("Time left", "Day / Time"))
                self.assertEqual(len(controller.applied), 10)
                loaded = Config.load(path)
                self.assertFalse(loaded.show_notification_pulse)
                self.assertEqual((loaded.clock_format, loaded.reset_display, loaded.compact_view,
                                  loaded.notification_color, loaded.font_scale), (12, "at", True, "violet", 115))
                self.assertEqual([font(15, font_scale=scale).pixelSize() for scale in (85, 100, 115)],
                                 [13, 15, 17])
                self.assertEqual((loaded.show_five_hour, loaded.show_weekly, loaded.language),
                                 (True, False, "en"))
                state = MockLimitProvider().get_state()
                blocks, _, fits, stacked = responsive_layout(340, 48, state, True,
                    reset_display="at", clock_format=12, compact_view=True, font_scale=115)
                self.assertTrue(fits)
                self.assertTrue(stacked)
                self.assertEqual(len(blocks), 2)
                self.assertTrue(all("bar" not in block for block in blocks))
                blocks, _, fits, stacked = responsive_layout(500, 48, state, True,
                    reset_display="at", clock_format=12, compact_view=False, language="en",
                    font_scale=115)
                self.assertTrue(fits)
                self.assertFalse(stacked)
                self.assertTrue(all("bar" in block for block in blocks))
                self.assertEqual([block["row"] for block in blocks], [(0, 48), (0, 48)])
                self.assertNotIn("/", blocks[0]["caption"])
                self.assertIn("/", blocks[1]["caption"])
                blocks, _, fits, _ = responsive_layout(500, 48, state, True,
                    reset_display="in", compact_view=False, language="tr")
                self.assertTrue(fits)
                self.assertTrue(all("bar" in block for block in blocks))
                blocks, _, fits, _ = responsive_layout(340, 48, state, True,
                    reset_display="in", compact_view=True, language="tr")
                self.assertTrue(fits)
                self.assertTrue(all(block["caption"].startswith("Reset: ") for block in blocks))
                self.assertEqual(len(blocks), 2)
                blocks, _, fits, _ = responsive_layout(500, 48, state, True,
                    reset_display="at", clock_format=12, compact_view=False, language="tr",
                    font_scale=115)
                self.assertTrue(fits)
                self.assertTrue(all("bar" in block for block in blocks))
                self.assertEqual([block["row"] for block in blocks], [(0, 48), (0, 48)])
                blocks, _, fits, _ = responsive_layout(340, 48, state, True,
                    reset_display="at", clock_format=12, show_weekly=False)
                self.assertTrue(fits)
                self.assertEqual([block["index"] for block in blocks], [0])
            finally:
                controls.settings.close()


if __name__ == "__main__":
    unittest.main()
