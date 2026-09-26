# LimitsHalo 0.1.0-beta — source

This source release shows remaining Codex 5-hour and weekly limits on the primary horizontal Windows taskbar. It needs a signed-in Codex Desktop session for live data. `--mock` and `--test` visibly label example values.

Local settings stay in an ignored `config.json`, initialized from `config.example.json` only when missing. Shutdown now waits for workers before closing the provider, and `--quit` works even if the config is invalid.

Automated tests, source and local PyInstaller startup/quit smoke checks, 240 px compact layout checks, and Turkish/English settings visual checks passed on the development Windows 11 machine. A clean Windows installation and separate Windows 10 or multi-monitor checks remain open. The local PyInstaller build was used only to verify bundled components and licenses. Installer and binary outputs are not part of this source release.

The PyInstaller configuration excludes unused GPL-only Qt components before collection, including Qt Virtual Keyboard. The local bundle inventory and dependency licenses are recorded in [third-party notices](THIRD_PARTY_NOTICES.md).

This is an unofficial community project, unaffiliated with OpenAI.
