param(
    [string]$Config = "configs/pl_PL-mateusz-medium.json",
    [switch]$Status,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$PythonExe = if (Test-Path $VenvPython -PathType Leaf) {
    $VenvPython
}
else {
    (Get-Command python.exe -ErrorAction Stop).Source
}

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

$ProcessExitCode = 1
Push-Location $ProjectDir
try {
    & $PythonExe @Arguments
    $ProcessExitCode = $LASTEXITCODE
}
finally {
    Pop-Location
}

exit $ProcessExitCode
