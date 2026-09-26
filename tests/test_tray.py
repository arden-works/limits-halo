import unittest

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from settings import Config
from tray import TrayControls


class FakeController(QObject):
    config_changed = Signal(object)

    def __init__(self):
        super().__init__()
        self.config = Config(language="en")
        self.refreshed = False

    def refresh(self):
        self.refreshed = True


class FakeSettings:
    def __init__(self):
        self.opened = False

    def show_settings(self):
        self.opened = True


class TrayTests(unittest.TestCase):
    def test_menu_actions_and_translation(self):
        app = QApplication.instance() or QApplication([])
        controller, settings = FakeController(), FakeSettings()
        quit_requests = []
        tray = TrayControls(app, controller, settings, lambda: quit_requests.append(True))
        try:
            self.assertFalse(tray.tray.icon().isNull())
            self.assertTrue(tray.tray.isVisible())
            self.assertEqual([action.text() for action in tray.menu.actions()],
                             ["Settings", "Refresh now", "Website - arden.ws", "", "Quit"])
            tray.settings_action.trigger()
            tray.refresh_action.trigger()
            self.assertTrue(settings.opened)
            self.assertTrue(controller.refreshed)
            tray.quit_action.trigger()
            self.assertEqual(quit_requests, [True])
            controller.config_changed.emit(Config(language="tr"))
            self.assertEqual([action.text() for action in tray.menu.actions()],
                             ["Ayarlar", "Şimdi yenile", "Website - arden.ws", "", "Çıkış Yap"])
        finally:
            tray.tray.hide()
            tray.menu.close()


if __name__ == "__main__":
    unittest.main()
