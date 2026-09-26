"""Opt-in, per-user Windows login registration, independent of UI."""
from pathlib import Path
import subprocess
import sys
import winreg
from paths import APP_NAME

KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
NAME = APP_NAME


def is_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY) as key:
            winreg.QueryValueEx(key, NAME)
            return True
    except FileNotFoundError:
        return False


def set_enabled(enabled: bool):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY) as key:
        if enabled:
            if getattr(sys, "frozen", False):
                command = subprocess.list2cmdline([sys.executable])
            else:
                pythonw = Path(sys.executable).with_name("pythonw.exe")
                if not pythonw.exists():
                    raise FileNotFoundError("pythonw.exe is required for a silent login launch")
                command = subprocess.list2cmdline([str(pythonw), str(Path(__file__).with_name("main.py").resolve())])
            winreg.SetValueEx(key, NAME, 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, NAME)
            except FileNotFoundError:
                pass
