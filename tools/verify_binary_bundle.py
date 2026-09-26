"""Check the local PyInstaller bundle before any binary release."""

import sys
from pathlib import Path


GPL_ONLY_MARKERS = (
    "canvaspainter", "coap", "graphs", "grpc", "httpserver", "lottie",
    "mqtt", "networkauth", "qmlcompiler", "quick3d", "quicktimeline",
    "virtualkeyboard", "waylandcompositor",
)
UNUSED_MARKERS = ("qt6pdf", "qpdf.dll", "qt6qml", "qt6quick")
REQUIRED_FILES = (
    "LimitsHalo.exe",
    "_internal/THIRD_PARTY_NOTICES.md",
    "_internal/LICENSE",
    "_internal/LICENSES/LGPL-3.0.txt",
    "_internal/PySide6/Qt6Core.dll",
    "_internal/PySide6/Qt6Gui.dll",
    "_internal/PySide6/Qt6Network.dll",
    "_internal/PySide6/Qt6Widgets.dll",
    "_internal/PySide6/plugins/platforms/qwindows.dll",
    "_internal/assets/codex-icon.svg",
)


def check(bundle: Path, analysis_toc: Path, collect_toc: Path) -> None:
    if not bundle.is_dir() or not analysis_toc.is_file() or not collect_toc.is_file():
        raise SystemExit("Missing PyInstaller bundle or build inventories")
    names = {path.relative_to(bundle).as_posix().lower()
             for path in bundle.rglob("*") if path.is_file()}
    missing = [name for name in REQUIRED_FILES if name.lower() not in names]
    if missing:
        raise SystemExit(f"Missing required bundled files: {missing}")

    markers = GPL_ONLY_MARKERS + UNUSED_MARKERS
    unwanted = sorted(name for name in names if any(marker in name for marker in markers))
    analysis = analysis_toc.read_text(encoding="utf-8").lower()
    unwanted_analysis = [marker for marker in GPL_ONLY_MARKERS if marker in analysis]
    toc = collect_toc.read_text(encoding="utf-8").lower()
    unwanted_toc = [marker for marker in markers if marker in toc]
    if unwanted_analysis or unwanted or unwanted_toc:
        raise SystemExit(f"Unwanted Qt components: Analysis={unwanted_analysis}; "
                         f"COLLECT={unwanted_toc}; bundle={unwanted}")
    print(f"PASS: {len(names)} files; required components and notices present; "
          "GPL-only components absent from Analysis; GPL-only and unused Qt "
          "components absent from COLLECT and bundle")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("Usage: verify_binary_bundle.py DIST/LimitsHalo "
                         "BUILD/LimitsHalo/Analysis-00.toc BUILD/LimitsHalo/COLLECT-00.toc")
    check(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
