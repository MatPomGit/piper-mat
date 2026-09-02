param(
    [string]$Config = "configs/pl_PL-mateusz-medium.json",
    [switch]$Status,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

$Arguments = @(
    "scripts/train_sessions.py",
    "--config",
    $Config
)

if ($Status) {
    $Arguments += "--status"
}
if ($DryRun) {
    $Arguments += "--dry-run"
}

Push-Location $ProjectDir
try {
    & $PythonExe @Arguments
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
