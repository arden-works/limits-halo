# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

project = Path(SPECPATH)
license_files = [(str(path), 'LICENSES') for path in sorted((project / 'LICENSES').glob('*.txt'))]
analysis = Analysis(
    ['main.py'],
    pathex=[str(project)],
    binaries=[],
    datas=[(str(project / 'assets' / 'codex-icon.svg'), 'assets'),
           (str(project / 'assets' / 'limitshalo-brand.ico'), 'assets'),
           (str(project / 'config.example.json'), '.'),
           (str(project / 'LICENSE'), '.'),
           (str(project / 'NOTICE'), '.'),
           (str(project / 'THIRD_PARTY_NOTICES.md'), '.'),
           *license_files],
    hiddenimports=[],
    hookspath=[str(project / 'hooks')],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
# The Codex bundled Python runtime has a Poppler ICU DLL on PATH. Its ICU 78
# exports do not match the Windows ICU bridge used by Qt, so keep it out.
def unused_qt_component(item):
    destination = item[0].replace('\\', '/').lower()
    return ('virtualkeyboard' in destination or
            destination.endswith('/qt6pdf.dll') or
            destination.endswith('/imageformats/qpdf.dll') or
            '/qt6qml' in destination or
            destination.endswith('/qt6quick.dll'))


# QtGui's built-in hook scans all platform input plugins. Our local hook keeps
# the unused virtual keyboard plugin out before Analysis. Any other GPL-only
# Qt component reaching Analysis is a blocker, not a file to silently delete.
gpl_only_modules = (
    'canvaspainter', 'coap', 'graphs', 'grpc', 'httpserver', 'lottie',
    'mqtt', 'networkauth', 'qmlcompiler', 'quick3d', 'quicktimeline',
    'virtualkeyboard', 'waylandcompositor',
)


def gpl_only_component(item):
    destination = item[0].replace('\\', '/').lower()
    return any(name in destination for name in gpl_only_modules)


# PDF/QML/Quick are also unused by this QWidget app; unlike Virtual Keyboard,
# these exclusions are for package size and unrelated third-party codecs.
required_gpl = [item[0] for item in (*analysis.pure, *analysis.binaries, *analysis.datas)
                if gpl_only_component(item)]
if required_gpl:
    raise RuntimeError(f'GPL-only Qt component reached Analysis: {required_gpl}')

analysis.binaries = [item for item in analysis.binaries
                     if item[0].lower() not in {'icuuc.dll', 'icudt78.dll'}
                     and not unused_qt_component(item)]
analysis.datas = [item for item in analysis.datas if not unused_qt_component(item)]
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz, analysis.scripts, [],
    exclude_binaries=True,
    name='LimitsHalo',
    console=False,
    icon=str(project / 'assets' / 'limitshalo-brand.ico'),
)
coll = COLLECT(exe, analysis.binaries, analysis.datas, strip=False, upx=False, name='LimitsHalo')
