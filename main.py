import argparse
import logging
from pathlib import Path
import sys
from paths import APP_NAME, data_dir, config_path


def main():
    parser = argparse.ArgumentParser(description="LimitsHalo · Windows taskbar overlay")
    parser.add_argument("--test", action="store_true", help="Right-click to cycle 5 / 40 / 72 / 88 / 97 / 100 percent")
    parser.add_argument("--mock", action="store_true", help="Use example data without test interactions")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--startup", choices=("enable", "disable"))
    parser.add_argument("--quit", action="store_true", help="Close the running instance")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("This overlay requires Windows 10/11")
    if args.startup:
        from startup import set_enabled
        set_enabled(args.startup == "enable")
        print(f"Windows login startup: {args.startup}d")
        return 0
    from PySide6.QtCore import QLockFile, QStandardPaths, QThread
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv[:1])
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)
    import getpass
    import hashlib
    name = "ai-limit-monitor-" + hashlib.sha256(getpass.getuser().encode()).hexdigest()[:16]
    if args.quit:
        socket = QLocalSocket()
        socket.connectToServer(name)
        if socket.waitForConnected(500):
            socket.write(b"quit\n")
            socket.waitForBytesWritten(500)
            socket.disconnectFromServer()
        return 0
    from settings import Config
    selected_config_path = args.config or config_path()
    try:
        config = Config.load(selected_config_path)
    except (OSError, ValueError, TypeError) as error:
        raise RuntimeError(f"Could not load {selected_config_path}: {error}") from error
    from logging.handlers import RotatingFileHandler
    handler = RotatingFileHandler(data_dir() / "widget.log", maxBytes=256_000, backupCount=1, encoding="utf-8")
    logging.basicConfig(level=logging.WARNING, handlers=[handler], format="%(asctime)s %(levelname)s %(message)s")
    lock = QLockFile(str(Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.TempLocation)) / f"{name}.lock"))
    if not lock.tryLock(0):
        print("LimitsHalo is already running.")
        return 0
    server = QLocalServer()
    server.setSocketOptions(QLocalServer.SocketOption.UserAccessOption)
    if not server.listen(name):
        lock.unlock()
        raise RuntimeError(f"Could not start local command server: {server.errorString()}")
    connections = {}
    def accept():
        while server.hasPendingConnections():
            socket = server.nextPendingConnection()
            connections[socket] = bytearray()
            def read(socket=socket):
                pending = connections.get(socket)
                if pending is None:
                    return
                pending.extend(bytes(socket.readAll()))
                if len(pending) > 64:
                    socket.disconnectFromServer()
                    return
                if b"\n" in pending:
                    command, _, _ = pending.partition(b"\n")
                    if command == b"quit":
                        stop_application()
                    socket.disconnectFromServer()
            def disconnected(socket=socket):
                pending = connections.pop(socket, None)
                if pending == b"quit":
                    stop_application()
                socket.deleteLater()
            socket.readyRead.connect(read)
            socket.disconnected.connect(disconnected)
            if socket.bytesAvailable():
                read()
    server.newConnection.connect(accept)
    from providers.mock import MockLimitProvider
    from providers.codex import CodexLimitProvider
    from windows.codex_launcher import toggle_codex_window
    from widget import LimitWidget
    from controller import Controller
    from settings_ui import SettingsControls
    from tray import TrayControls
    provider = (MockLimitProvider(config.mock_five_hour_percent, config.mock_weekly_percent)
                if args.test or args.mock else CodexLimitProvider())
    widget = LimitWidget(config, is_mock=provider.is_mock, test_mode=args.test)
    controller = Controller(widget, provider, config)
    settings_controls = SettingsControls(controller, selected_config_path)
    shutting_down = False
    def stop_application():
        nonlocal shutting_down
        if shutting_down:
            return
        shutting_down = True
        def finish():
            # A Qt window parented to Explorer must be detached before quit.
            widget.windowHandle().setParent(None)
            controller.taskbar_window = None
            app.quit()
        controller.stop(finish)
    tray = TrayControls(app, controller, settings_controls, stop_application)
    def toggle_codex_from_widget():
        if controller.stopping:
            return
        events = controller.events
        foreground, taskbar = events.last_non_taskbar_foreground, events.taskbar_hwnd
        controller.start_worker(
            "codex-launcher",
            lambda: toggle_codex_window(foreground, taskbar))
    widget.launch_requested.connect(toggle_codex_from_widget)
    def ensure_shutdown():
        if not controller.stopping:
            controller.stop(lambda: None)
        while controller._stopped_callback is not None:
            app.processEvents()
            QThread.msleep(10)
    app.aboutToQuit.connect(ensure_shutdown)
    app.aboutToQuit.connect(widget.close)
    app.aboutToQuit.connect(settings_controls.settings.close)
    app.aboutToQuit.connect(tray.tray.hide)
    result = app.exec()
    server.close()
    for socket in list(connections):
        socket.disconnectFromServer()
        socket.deleteLater()
    connections.clear()
    lock.unlock()
    return result


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        logging.exception("LimitsHalo startup failed")
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, str(error), "LimitsHalo could not start", 0x10)
        raise SystemExit(1)
