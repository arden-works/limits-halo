"""Render a clearly labelled example of the production widget for README."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QPoint
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtWidgets import QApplication
from models import LimitState
from settings import Config
from widget import LimitWidget, text


def main():
    app = QApplication([])
    now = datetime.now(timezone.utc)
    with patch("widget.apply_overlay_style"):
        widget = LimitWidget(Config(), is_mock=True)
    widget.set_state(LimitState(72, now + timedelta(hours=2, minutes=14),
                                31, now + timedelta(days=2, hours=3), now))
    widget.resize(500, 48)
    image = QImage(800, 350, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(QColor("#642833"))
    painter = QPainter(image)
    text(painter, (28, 18, 700, 25), "Example data · Windows accent color illustration", QColor("#fff6f6"), 13)
    widget.render(painter, QPoint(28, 55))
    painter.end()
    output = Path(__file__).resolve().parents[1] / "docs" / "preview.png"
    output.parent.mkdir(exist_ok=True)
    if not image.save(str(output)):
        raise RuntimeError("Could not save preview")
    widget.close()
    app.quit()


if __name__ == "__main__":
    main()
