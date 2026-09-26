"""Localized settings window opened from the notification area."""
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QButtonGroup, QCheckBox, QDialog, QFrame,
                               QGridLayout, QLabel, QMessageBox, QVBoxLayout,
                               QRadioButton, QWidget)

from i18n import tr
from paths import APP_NAME
from settings import NOTIFICATION_COLORS
from startup import is_enabled, set_enabled

SETTINGS_THEME = """
QDialog { background: #17191d; color: #e9eaec; font-family: 'Bahnschrift'; font-size: 14px; }
QLabel { color: #c8cdd3; font-size: 14px; font-weight: 600; }
QCheckBox, QRadioButton { color: #e5e7ea; font-size: 14px; font-weight: 400;
                          spacing: 8px; padding: 4px 0; }
QRadioButton:disabled { color: #858b93; }
QRadioButton::indicator { width: 16px; height: 16px; border: 1px solid #777e87;
                          border-radius: 5px; background: #24272c; }
QRadioButton::indicator:hover { border-color: #a7adb5; }
QRadioButton::indicator:checked { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                   stop:0 #e08a40, stop:1 #bd6326);
                                   border-color: #d4772e; }
QRadioButton[choiceColor="amber"]::indicator:checked { background: #ffb143; border-color: #ffb143; }
QRadioButton[choiceColor="coral"]::indicator:checked { background: #ff6b6b; border-color: #ff6b6b; }
QRadioButton[choiceColor="pink"]::indicator:checked { background: #ff65bd; border-color: #ff65bd; }
QRadioButton[choiceColor="violet"]::indicator:checked { background: #a782ff; border-color: #a782ff; }
QRadioButton[choiceColor="cyan"]::indicator:checked { background: #43d8e8; border-color: #43d8e8; }
QRadioButton[choiceColor="lime"]::indicator:checked { background: #b7ed5b; border-color: #b7ed5b; }
QRadioButton[choiceColor="none"]::indicator:checked { background: #858b93; border-color: #858b93; }
QRadioButton::indicator:disabled { background: #30343a; border-color: #484d55; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #777e87;
                       border-radius: 5px; background: #24272c; }
QCheckBox::indicator:checked { background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                                stop:0 #e08a40, stop:1 #bd6326); border-color: #d4772e; }
QCheckBox::indicator:disabled { background: #30343a; border-color: #484d55; }
QFrame#separator { background: #34383e; border: 0; max-height: 1px; }
"""


class RadioChoices(QWidget):
    def __init__(self, options, columns=2, cell_width=250):
        super().__init__()
        self.group = QButtonGroup(self)
        self.options = options
        self.buttons = []
        layout = QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(18)
        layout.setVerticalSpacing(6)
        for column in range(columns):
            layout.setColumnMinimumWidth(column, cell_width)
        layout.setColumnStretch(columns - 1, 1)
        for index, (value, _) in enumerate(options):
            button = QRadioButton()
            button.setFixedWidth(260 if value is None else cell_width)
            if value in NOTIFICATION_COLORS or value is None:
                button.setProperty("choiceColor", value or "none")
            self.group.addButton(button, index)
            self.buttons.append(button)
            span = 2 if value is None else 1
            layout.addWidget(button, index // columns, index % columns, 1, span,
                             Qt.AlignmentFlag.AlignLeft)

    def currentData(self):
        index = self.group.checkedId()
        return self.options[index][0] if index >= 0 else None

    def setCurrentData(self, value):
        for index, (option, _) in enumerate(self.options):
            if option == value:
                self.buttons[index].setChecked(True)
                return

    def setLabels(self, language):
        for button, (_, key) in zip(self.buttons, self.options):
            button.setText(tr(key, language) if key else button.text())


class SettingsWindow(QDialog):
    def __init__(self, controls, icon):
        super().__init__()
        self.controls = controls
        self.setWindowIcon(icon)
        self.setFixedWidth(760)
        self.setStyleSheet(SETTINGS_THEME)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        layout = QGridLayout(self)
        layout.setContentsMargins(26, 23, 26, 25)
        layout.setHorizontalSpacing(24)
        layout.setVerticalSpacing(14)
        layout.setColumnMinimumWidth(0, 130)
        layout.setColumnStretch(1, 1)

        self.language_label = QLabel()
        self.language = RadioChoices((("tr", None), ("en", None)))
        self.language.buttons[0].setText("Türkçe")
        self.language.buttons[1].setText("English")
        layout.addWidget(self.language_label, 0, 0)
        layout.addWidget(self.language, 0, 1)

        self.limits_label = QLabel()
        limit_choices = QWidget()
        limits_layout = QGridLayout(limit_choices)
        limits_layout.setContentsMargins(0, 0, 0, 0)
        limits_layout.setHorizontalSpacing(18)
        limits_layout.setColumnMinimumWidth(0, 250)
        limits_layout.setColumnMinimumWidth(1, 250)
        limits_layout.setColumnStretch(1, 1)
        self.five = QCheckBox()
        self.week = QCheckBox()
        self.five.setFixedWidth(250)
        self.week.setFixedWidth(250)
        limits_layout.addWidget(self.five, 0, 0, Qt.AlignmentFlag.AlignLeft)
        limits_layout.addWidget(self.week, 0, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.limits_label, 1, 0)
        layout.addWidget(limit_choices, 1, 1)
        self._separator(layout, 2)

        self.view_label = QLabel()
        self.view = RadioChoices(((False, "normal"), (True, "compact")))
        layout.addWidget(self.view_label, 3, 0)
        layout.addWidget(self.view, 3, 1)
        self.reset_label = QLabel()
        self.reset = RadioChoices((("in", "remaining"), ("at", "clock_time")))
        layout.addWidget(self.reset_label, 4, 0)
        layout.addWidget(self.reset, 4, 1)
        self.clock_label = QLabel()
        self.clock = RadioChoices(((12, "hours_12"), (24, "hours_24")))
        layout.addWidget(self.clock_label, 5, 0)
        layout.addWidget(self.clock, 5, 1)
        self.font_label = QLabel()
        self.font_size = RadioChoices(((85, "font_small"), (100, "font_default"),
                                       (115, "font_large")), columns=3, cell_width=160)
        layout.addWidget(self.font_label, 6, 0)
        layout.addWidget(self.font_size, 6, 1)
        self._separator(layout, 7)

        self.color_label = QLabel()
        self.color = RadioChoices(tuple((key, key) for key in NOTIFICATION_COLORS) +
                                  ((None, "notification_none"),))
        layout.addWidget(self.color_label, 8, 0, Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.color, 8, 1)
        self._separator(layout, 9)

        self.startup = QCheckBox()
        layout.addWidget(self.startup, 10, 1)
        footer = QWidget()
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.setSpacing(3)
        self.project_credit = QLabel("Arden Works Project")
        self.project_credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.project_links = QLabel(
            '<a href="https://arden.ws" style="color:#aab4c1; text-decoration:underline;">arden.ws</a>'
            '  ·  '
            '<a href="https://github.com/arden-works/" '
            'style="color:#aab4c1; text-decoration:underline;">github</a>')
        self.project_links.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.project_links.setTextFormat(Qt.TextFormat.RichText)
        self.project_links.setOpenExternalLinks(True)
        self.project_links.setTextInteractionFlags(Qt.TextInteractionFlag.LinksAccessibleByMouse)
        footer_layout.addWidget(self.project_credit)
        footer_layout.addWidget(self.project_links)
        layout.addWidget(footer, 11, 0, 1, 2)
        for label in (self.language_label, self.limits_label, self.view_label,
                      self.reset_label, self.clock_label, self.font_label, self.color_label):
            label.setFixedWidth(150)

        self.sync(controls.controller.config)
        self.startup.setChecked(is_enabled())
        self.language.group.idClicked.connect(
            lambda _: controls.change_setting("language", self.language.currentData()))
        self.five.toggled.connect(lambda value: controls.change_setting("show_five_hour", value))
        self.week.toggled.connect(lambda value: controls.change_setting("show_weekly", value))
        self.view.group.idClicked.connect(
            lambda _: controls.change_setting("compact_view", self.view.currentData()))
        self.reset.group.idClicked.connect(
            lambda _: controls.change_reset(self.reset.currentData()))
        self.clock.group.idClicked.connect(
            lambda _: controls.change_setting("clock_format", self.clock.currentData()))
        self.font_size.group.idClicked.connect(
            lambda _: controls.change_setting("font_scale", self.font_size.currentData()))
        self.color.group.idClicked.connect(
            lambda _: controls.change_notification(self.color.currentData()))
        self.startup.toggled.connect(controls.toggle_startup)

    @staticmethod
    def _separator(layout, row):
        line = QFrame()
        line.setObjectName("separator")
        line.setFixedHeight(1)
        layout.addWidget(line, row, 0, 1, 2)

    def sync(self, config):
        self.setStyleSheet(SETTINGS_THEME.replace("14px", f"{round(14 * config.font_scale / 100)}px"))
        title_size = round(12 * config.font_scale / 100)
        link_size = round(11 * config.font_scale / 100)
        self.project_credit.setStyleSheet(
            f"color: #b9bec5; font-size: {title_size}px; font-weight: 600;")
        self.project_links.setStyleSheet(
            f"color: #9099a4; font-size: {link_size}px; font-weight: 400;")
        checks = ((self.five, config.show_five_hour), (self.week, config.show_weekly))
        for control, value in checks:
            control.blockSignals(True)
            control.setChecked(value)
            control.blockSignals(False)
        choices = ((self.language, config.language), (self.view, config.compact_view),
                   (self.reset, config.reset_display), (self.clock, config.clock_format),
                   (self.font_size, config.font_scale),
                   (self.color, config.notification_color if config.show_notification_pulse else None))
        for control, value in choices:
            control.setCurrentData(value)
        self.retranslate(config.language)

    def retranslate(self, language):
        self.setWindowTitle(f"{APP_NAME} · {tr('settings', language)}")
        for target, key in ((self.language_label, "language"), (self.limits_label, "limits"),
                            (self.five, "five"), (self.week, "week"),
                            (self.view_label, "view"), (self.reset_label, "reset_mode"),
                            (self.clock_label, "clock_format"), (self.font_label, "font_size"),
                            (self.color_label, "color"),
                            (self.startup, "startup")):
            target.setText(tr(key, language))
        for choices in (self.view, self.reset, self.clock, self.font_size, self.color):
            choices.setLabels(language)


class SettingsControls:
    def __init__(self, controller, config_file):
        self.controller = controller
        self.config_file = Path(config_file)
        icon = QIcon(str(Path(__file__).resolve().parent / "assets" / "limitshalo-brand.ico"))
        self.settings = SettingsWindow(self, icon)

    def show_settings(self):
        self.settings.startup.blockSignals(True)
        self.settings.startup.setChecked(is_enabled())
        self.settings.startup.blockSignals(False)
        self.settings.showNormal()
        self.settings.raise_()
        self.settings.activateWindow()

    def change_setting(self, name, value):
        self.change_settings(**{name: value})

    def change_reset(self, value):
        self.change_settings(reset_display=value, show_countdown=True)

    def change_notification(self, value):
        if value is None:
            self.change_settings(show_notification_pulse=False)
        else:
            self.change_settings(notification_color=value, show_notification_pulse=True)

    def change_settings(self, **changes):
        previous = self.controller.config
        updated = replace(previous, **changes)
        if not (updated.show_five_hour or updated.show_weekly):
            self.settings.sync(previous)
            return
        try:
            updated.save(self.config_file)
        except OSError as error:
            self.settings.sync(previous)
            QMessageBox.warning(self.settings, APP_NAME,
                                f"{tr('saving_failed', previous.language)}: {error}")
            return
        self.controller.apply_config(updated)
        self.settings.sync(updated)

    def toggle_startup(self, checked):
        try:
            set_enabled(checked)
        except OSError as error:
            self.settings.startup.blockSignals(True)
            self.settings.startup.setChecked(is_enabled())
            self.settings.startup.blockSignals(False)
            QMessageBox.warning(self.settings, APP_NAME,
                                f"{tr('startup_failed', self.controller.config.language)}: {error}")
