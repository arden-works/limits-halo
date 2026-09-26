# LimitsHalo

[English](README.md) / [Türkçe](README.tr.md)

**Keep your Codex usage limits visible on the Windows taskbar.**

LimitsHalo shows your remaining **5-hour and weekly Codex limits** directly on the taskbar, so you don't need to open Codex or manually check your usage.

It uses your existing signed-in Codex Desktop session locally. **No API key is required.**

## Screenshots

![Normal widget and settings](docs/screenshots/settings-normal.png)
![Compact widget and settings](docs/screenshots/settings-compact.png)
![Turkish taskbar widget](docs/screenshots/widget-turkish.png)

## Download

Download the latest Windows installer from [GitHub Releases](https://github.com/arden-works/limits-halo/releases).

> The installer is currently unsigned, so Windows SmartScreen may display a warning.

## How to use

- Your remaining 5-hour and weekly limits are shown directly on the Windows taskbar.
- Click the Codex icon to open, focus, or minimize Codex.
- Open the tray menu to access **Settings**, refresh usage, manage startup behavior, or quit LimitsHalo.
- Settings are stored locally on your computer.

## Requirements

- Windows 11 (verified); Windows 10 has not been verified
- Codex Desktop installed and signed in

## Run from source

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

On first run, `config.example.json` is copied to the local, ignored `config.json` if it does not exist. Run `main.py --quit` to close the widget. For development, `--mock` and `--test` show visibly marked example data; `--test` also lets you cycle sample percentages with a right-click.

## Known limitations

- Currently targets the primary horizontal Windows taskbar.
- Windows 10 and multi-monitor behavior have not been fully verified.
- LimitsHalo only displays limits provided by Codex; it does not estimate missing usage data.
- Notification animation depends on Windows' local notification data.

## License

LimitsHalo source code is licensed under the [Apache License 2.0](LICENSE). Copyright (c) 2026 Arden Works; see [NOTICE](NOTICE).

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for third-party components and trademarks.

LimitsHalo is an independent project and is not affiliated with or endorsed by OpenAI.
