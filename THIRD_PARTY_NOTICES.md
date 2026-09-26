# Third-party notices

LimitsHalo's source code is licensed under the [Apache License 2.0](LICENSE); see the project [NOTICE](NOTICE). These notices describe third-party components found in the local Windows PyInstaller verification build; that build is not published. `requirements.txt` installs PySide6 6.11.2 and its Shiboken6 and Qt dependencies.

| Bundled component | Files or role | License basis |
| --- | --- | --- |
| Python 3.12.14 | `python312.dll`, standard-library binaries and archive | Python Software Foundation License ([text](LICENSES/Python-PSF.txt)) |
| PySide6, PySide6 Essentials/Addons, Shiboken6 6.11.2 | Python bindings and supporting libraries | Installed wheel metadata offers `LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only`; this project uses the LGPLv3 option ([LGPLv3](LICENSES/LGPL-3.0.txt), [incorporated GPLv3 text](LICENSES/GPL-3.0.txt)) |
| Qt 6.11.2 | `Qt6Core`, `Qt6Gui`, `Qt6Network`, `Qt6OpenGL`, `Qt6Svg`, `Qt6Widgets` DLLs and the bundled platform, style, image, network, and TLS plugins | These modules are available under LGPLv3 (also GPL or commercial alternatives); see [Qt licensing](https://doc.qt.io/qt-6/licensing.html) and [component notices](https://doc.qt.io/qt-6/licenses-used-in-qt.html) |
| Qt's bundled codecs and data | The included image-format and network plugins may incorporate libjpeg-turbo (IJG/BSD), libtiff (libtiff), libwebp (BSD-3-Clause), XSVG (HPND), and Public Suffix List data (MPL-2.0) | [Qt GUI](https://doc.qt.io/qt-6/qtgui-index.html), [Image Formats](https://doc.qt.io/qt-6/qtimageformats-index.html), [SVG](https://doc.qt.io/qt-6/qtsvg-index.html), [Network](https://doc.qt.io/qt-6/qtnetwork-index.html) |
| Mesa llvmpipe | `opengl32sw.dll`, Qt's software OpenGL fallback | MIT and Boost Software License 1.0 ([Qt attribution](https://doc.qt.io/qt-6/qt-attribution-llvmpipe.html)) |
| OpenSSL 3.6.4 | `libcrypto-3-x64.dll`, `libssl-3-x64.dll` | [Apache-2.0](https://openssl-library.org/source/license/); version read from the bundled DLLs |
| libffi | `libffi-8.dll` | [MIT-style license](https://github.com/libffi/libffi/blob/master/LICENSE) |
| SQLite | `sqlite3.dll` | [Public domain](https://www.sqlite.org/copyright.html) |
| PyInstaller 6.22.3 bootloader | `LimitsHalo.exe` bootloader | GPL-2.0-or-later with the bootloader exception ([text](LICENSES/PyInstaller-COPYING.txt), [explanation](https://pyinstaller.org/en/stable/license.html)) |
| Microsoft Visual C++ / Universal CRT | `MSVCP*`, `VCRUNTIME*`, `ucrtbase.dll`, Windows API-set DLLs | [Microsoft redistribution terms](https://learn.microsoft.com/en-us/cpp/windows/redistributing-visual-cpp-files?view=msvc-170) |

The Qt GPLv3-only Virtual Keyboard module is unused. A local PyInstaller hook prevents `qtvirtualkeyboardplugin.dll` and its `Qt6VirtualKeyboard.dll` dependency from entering Analysis; the spec aborts if any GPL-only Qt component still reaches Analysis. Other unused Qt PDF, QML, and Quick files are excluded before final collection. The GPLv3 license text remains in `LICENSES` because LGPLv3 incorporates its terms; its presence does not mean a GPL-only runtime component is bundled. A required GPL-only component must be treated as a release blocker, not silently removed. Any future binary release needs a fresh inventory and license review.

## Codex icon

`assets/codex-icon.svg` is the Codex icon, not the LimitsHalo app icon. It appears beside Codex limit data solely to identify the service those limits come from. The icon retains its original shape and proportions and is displayed in monochrome white; no other color is applied to it. The notification pulse is drawn as a separate glow behind the icon. Codex and its marks belong to OpenAI. This asset is not covered by this project's Apache License 2.0. LimitsHalo is independent of and not endorsed by OpenAI. See [OpenAI's brand guidelines](https://openai.com/brand/) for mark usage terms.
