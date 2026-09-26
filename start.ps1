param([switch]$TestMode)
$ErrorActionPreference = 'Stop'
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $taskPython)) {
    $taskBasePython = Get-Command python -ErrorAction SilentlyContinue
    if (-not $taskBasePython -or $taskBasePython.Source -like '*WindowsApps*') {
        throw 'Python 3.10+ kurun, sonra python -m venv .venv ve .venv\Scripts\python -m pip install -r requirements.txt komutlarını çalıştırın.'
    }
    & $taskBasePython.Source -m venv (Join-Path $PSScriptRoot '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Sanal ortam oluşturulamadı.' }
    & (Join-Path $PSScriptRoot '.venv\Scripts\python.exe') -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'PySide6 kurulamadı.' }
}
$taskArgs = @('"' + (Join-Path $PSScriptRoot 'main.py') + '"')
if ($TestMode) { $taskArgs += '--test' }
Start-Process -FilePath $taskPython -ArgumentList $taskArgs -WorkingDirectory $PSScriptRoot -WindowStyle Hidden
