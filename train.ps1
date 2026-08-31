param(
    [string]$Config = "configs/pl_PL-mateusz-medium.json",
    [switch]$Status,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$argsList = @("scripts/train_sessions.py", "--config", $Config)
if ($Status) { $argsList += "--status" }
if ($DryRun) { $argsList += "--dry-run" }

python @argsList
exit $LASTEXITCODE
