$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$taskRelease = Join-Path $taskRoot 'artifacts\release'
$taskStage = [System.IO.Path]::GetFullPath((Join-Path $taskRoot 'artifacts\public-source'))
if (-not $taskStage.StartsWith($taskRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Stage path must stay inside this workspace.'
}
if (Test-Path -LiteralPath $taskStage) { Remove-Item -LiteralPath $taskStage -Recurse -Force }
New-Item -ItemType Directory -Path $taskStage -Force | Out-Null
$taskFiles = @(
    '.gitignore','README.md','LICENSE','NOTICE','THIRD_PARTY_NOTICES.md','RELEASE_NOTES.md','requirements.txt','config.example.json',
    'LICENSES/GPL-3.0.txt','LICENSES/LGPL-3.0.txt','LICENSES/PyInstaller-COPYING.txt','LICENSES/Python-PSF.txt',
    'main.py','paths.py','settings.py','settings_ui.py','i18n.py','startup.py','start.ps1','build.ps1','package-source.ps1',
    'LimitsHalo.spec','controller.py','models.py','time_helpers.py','widget.py',
    'hooks/hook-PySide6.QtGui.py',
    'assets/codex-icon.svg','assets/limitshalo-brand.ico','assets/limitshalo-brand-light.ico',
    'tools/generate_preview.py','tools/make_limits_halo_brand_icon.py','tools/verify_binary_bundle.py',
    'providers/__init__.py','providers/base.py','providers/codex.py','providers/mock.py',
    'windows/__init__.py','windows/accessibility.py','windows/codex_launcher.py',
    'windows/events.py','windows/notifications.py','windows/taskbar.py',
    'tests/test_core.py','tests/test_codex.py','tests/test_controller.py','tests/test_notifications.py',
    'tests/test_settings_ui.py','tests/test_tray.py','tests/test_widget_modes.py',
    'tests/verify_ui.py','tests/verify_zorder.py','tests/window_fixture.py'
)
foreach ($taskRelative in $taskFiles) {
    $taskSource = Join-Path $taskRoot $taskRelative
    if (-not (Test-Path -LiteralPath $taskSource)) { throw "Missing source file: $taskRelative" }
    $taskDestination = Join-Path $taskStage $taskRelative
    New-Item -ItemType Directory -Path (Split-Path -Parent $taskDestination) -Force | Out-Null
    Copy-Item -LiteralPath $taskSource -Destination $taskDestination
}
New-Item -ItemType Directory -Path $taskRelease -Force | Out-Null
$taskZip = Join-Path $taskRelease 'LimitsHalo-0.1.0-beta-source.zip'
if (Test-Path -LiteralPath $taskZip) { Remove-Item -LiteralPath $taskZip -Force }
Compress-Archive -Path (Join-Path $taskStage '*') -DestinationPath $taskZip -CompressionLevel Optimal
Write-Output $taskZip
