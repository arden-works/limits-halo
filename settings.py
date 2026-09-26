from dataclasses import dataclass, fields
from pathlib import Path
import json
import math
import os
import tempfile


NOTIFICATION_COLORS = {
    "amber": ("Amber", "#ffb143"),
    "coral": ("Mercan", "#ff6b6b"),
    "pink": ("Pembe", "#ff65bd"),
    "violet": ("Mor", "#a782ff"),
    "cyan": ("Turkuaz", "#43d8e8"),
    "lime": ("Yeşil", "#b7ed5b"),
}


@dataclass(frozen=True)
class Config:
    offset_x: int = 0
    opacity: float = 0.96
    show_countdown: bool = True
    show_widget: bool = True
    show_notification_pulse: bool = True
    clock_format: int = 24
    font_scale: int = 100
    reset_display: str = "in"
    compact_view: bool = False
    notification_color: str = "amber"
    language: str = "tr"
    show_five_hour: bool = True
    show_weekly: bool = True
    width: int = 600
    safe_right_x: int | None = None
    mock_five_hour_percent: float = 72
    mock_weekly_percent: float = 31

    @classmethod
    def load(cls, path: Path):
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError("config.json must contain an object")
        unknown = set(data) - {f.name for f in fields(cls)}
        if unknown:
            raise ValueError(f"Unknown settings: {', '.join(sorted(unknown))}")
        cfg = cls(**data)
        for name, low, high in (("offset_x", 0, 4000), ("width", 240, 600),
                                ("opacity", .2, 1), ("mock_five_hour_percent", 0, 100),
                                ("mock_weekly_percent", 0, 100)):
            value = getattr(cfg, name)
            if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
                raise ValueError(f"{name} must be between {low} and {high}")
        if type(cfg.offset_x) is not int or type(cfg.width) is not int:
            raise ValueError("offset_x and width must be integers")
        for name in ("show_countdown", "show_widget", "show_notification_pulse", "compact_view",
                     "show_five_hour", "show_weekly"):
            if type(getattr(cfg, name)) is not bool:
                raise ValueError(f"{name} must be true or false")
        if not (cfg.show_five_hour or cfg.show_weekly):
            raise ValueError("At least one limit must be shown")
        if cfg.language not in ("tr", "en"):
            raise ValueError("language must be tr or en")
        if type(cfg.clock_format) is not int or cfg.clock_format not in (12, 24):
            raise ValueError("clock_format must be 12 or 24")
        if type(cfg.font_scale) is not int or cfg.font_scale not in (85, 100, 115):
            raise ValueError("font_scale must be 85, 100 or 115")
        if cfg.reset_display not in ("in", "at"):
            raise ValueError("reset_display must be in or at")
        if cfg.notification_color not in NOTIFICATION_COLORS:
            raise ValueError("Unknown notification_color")
        if cfg.safe_right_x is not None and (type(cfg.safe_right_x) is not int or cfg.safe_right_x < 1):
            raise ValueError("safe_right_x must be a positive integer or null")
        return cfg

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix="config-", suffix=".json", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                json.dump({field.name: getattr(self, field.name) for field in fields(self)}, stream, indent=2)
                stream.write("\n")
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
