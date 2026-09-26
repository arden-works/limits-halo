# LimitsHalo

[English](README.md) / [Türkçe](README.tr.md)

LimitsHalo is an unofficial Windows taskbar widget for remaining Codex 5-hour and weekly limits. It reads the signed-in Codex Desktop session through the local Codex app-server. The tray icon opens settings and offers refresh and quit. This source release is `0.1.0-beta`.

## Run from source

Use Windows 10 or 11 and Python 3.10 or newer:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Codex Desktop must be installed and signed in for live limits. On first run, `config.example.json` is copied to a local, ignored `config.json`. Run `main.py --quit` to close the widget. `main.py --mock` and `main.py --test` display visibly marked example data; `--test` also lets right-click cycle sample percentages.

## Limits

The widget supports the primary horizontal taskbar. It never estimates a limit that Codex does not provide. Notification animation depends on Windows' local notification database and may stop working if that database changes. Separate Windows 10, multi-monitor, and clean-machine behavior has not been verified. All-time token usage is not requested or displayed.

## License

LimitsHalo source code is licensed under the [Apache License 2.0](LICENSE). Copyright (c) 2026 Arden Works; see [NOTICE](NOTICE). See [third-party notices](THIRD_PARTY_NOTICES.md) for dependencies. Codex names and marks belong to OpenAI; this project is not affiliated with OpenAI.
