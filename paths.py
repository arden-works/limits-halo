"""Separate bundled read-only files from per-user writable files."""
import os
from pathlib import Path
import sys


RESOURCE_DIR = Path(__file__).resolve().parent
APP_NAME = "LimitsHalo"


def data_dir() -> Path:
    if getattr(sys, "frozen", False):
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home() / "AppData" / "Local")
        path = base / APP_NAME
        path.mkdir(parents=True, exist_ok=True)
        return path
    return RESOURCE_DIR


def config_path() -> Path:
    target = data_dir() / "config.json"
    if not target.exists():
        target.write_bytes((RESOURCE_DIR / "config.example.json").read_bytes())
    return target
