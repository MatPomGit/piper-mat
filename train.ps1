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

$PreviousPythonUtf8 = $env:PYTHONUTF8
$ProcessExitCode = 1
Push-Location $ProjectDir
try {
    $env:PYTHONUTF8 = "1"
    & $PythonExe @Arguments
    $ProcessExitCode = $LASTEXITCODE
}
finally {
    if ($null -eq $PreviousPythonUtf8) {
        Remove-Item Env:PYTHONUTF8 -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONUTF8 = $PreviousPythonUtf8
    }
    Pop-Location
}

exit $ProcessExitCode
