"""Create L-in-a-halo Windows icon variants for LimitsHalo."""
from pathlib import Path

from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SIZE = 1024
SCALE = SIZE / 256
SIZES = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def box(*coords):
    return tuple(round(value * SCALE) for value in coords)


def make_icon(filename, background, border, halo, accent, letter):
    canvas = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle(box(10, 10, 246, 246), radius=round(56 * SCALE), fill=background)
    draw.rounded_rectangle(
        box(12, 12, 244, 244), radius=round(54 * SCALE),
        outline=border, width=round(2 * SCALE),
    )

    # Keep the circular halo around the initial.
    ring = box(44, 44, 212, 212)
    draw.arc(ring, 130, 410, fill=halo, width=round(19 * SCALE))
    draw.arc(ring, 414, 468, fill=accent, width=round(19 * SCALE))

    # One broad L remains legible in the Windows notification area.
    draw.rounded_rectangle(box(99, 84, 119, 166), radius=round(8 * SCALE), fill=letter)
    draw.rounded_rectangle(box(102, 146, 161, 166), radius=round(8 * SCALE), fill=letter)

    output = ROOT / "assets" / filename
    canvas.save(output, format="ICO", sizes=SIZES)
    print(output)


make_icon("limitshalo-brand.ico", "#111216", "#38312B", "#F58220", "#FFB65B", "#FFF7EB")
make_icon("limitshalo-brand-light.ico", "#FFF9F1", "#E6D8C7", "#E76F16", "#FFAB45", "#211B17")
