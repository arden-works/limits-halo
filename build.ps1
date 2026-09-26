$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw 'Project virtual environment is missing.' }
Push-Location $PSScriptRoot
try {
    & $taskPython -m PyInstaller --noconfirm --clean (Join-Path $PSScriptRoot 'LimitsHalo.spec')
    if ($LASTEXITCODE -ne 0) { throw 'PyInstaller build failed.' }
    $taskIscc = @(
        'C:\Program Files (x86)\Inno Setup 6\ISCC.exe',
        'C:\Program Files\Inno Setup 6\ISCC.exe',
        (Join-Path $env:LOCALAPPDATA 'Programs\Inno Setup 6\ISCC.exe')
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (-not $taskIscc) { throw 'Inno Setup 6 ISCC.exe was not found.' }
    & $taskIscc (Join-Path $PSScriptRoot 'installer\LimitsHalo.iss')
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }
}
finally { Pop-Location }
