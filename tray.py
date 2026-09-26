"""Notification-area access to settings and application actions."""
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from i18n import tr
from paths import APP_NAME


class TrayControls:
    def __init__(self, app, controller, settings_controls, stop_application):
        self.controller = controller
        self.settings_controls = settings_controls
        icon = QIcon(str(Path(__file__).resolve().parent / "assets" / "limitshalo-brand.ico"))
        self.tray = QSystemTrayIcon(icon, app)
        self.tray.setToolTip(APP_NAME)
        self.menu = QMenu()
        self.settings_action = self.menu.addAction("")
        self.settings_action.triggered.connect(settings_controls.show_settings)
        self.refresh_action = self.menu.addAction("")
        self.refresh_action.triggered.connect(controller.refresh)
        self.website_action = self.menu.addAction("Website - arden.ws")
        self.website_action.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://arden.ws")))
        self.menu.addSeparator()
        self.quit_action = self.menu.addAction("")
        self.quit_action.triggered.connect(stop_application)
        self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_activated)
        controller.config_changed.connect(lambda config: self.retranslate(config.language))
        self.retranslate(controller.config.language)
        self.tray.show()

    def retranslate(self, language):
        self.settings_action.setText(tr("settings", language))
        self.refresh_action.setText(tr("refresh", language))
        self.quit_action.setText(tr("quit", language))

    def on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.menu.popup(self.tray.geometry().bottomLeft())
