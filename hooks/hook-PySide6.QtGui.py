"""Keep the unused GPL-only virtual keyboard out of QtGui collection."""

from PyInstaller.utils.hooks.qt import add_qt6_dependencies


hiddenimports, binaries, datas = add_qt6_dependencies(__file__)
hiddenimports = [name for name in hiddenimports if "virtualkeyboard" not in name.lower()]
binaries = [(source, target) for source, target in binaries
            if "virtualkeyboard" not in source.lower()
            and "virtualkeyboard" not in target.lower()]
datas = [(source, target) for source, target in datas
         if "virtualkeyboard" not in source.lower()
         and "virtualkeyboard" not in target.lower()]
