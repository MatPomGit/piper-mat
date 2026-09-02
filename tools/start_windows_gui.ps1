$ErrorActionPreference = "Stop"
Add-Type -AssemblyName PresentationFramework

function Show-Info {
    param([Parameter(Mandatory)][string]$Message)
    [System.Windows.MessageBox]::Show(
        $Message,
        "piper-mat",
        "OK",
        "Information"
    ) | Out-Null
}

function Show-ErrorMessage {
    param([Parameter(Mandatory)][string]$Message)
    [System.Windows.MessageBox]::Show(
        $Message,
        "piper-mat",
        "OK",
        "Error"
    ) | Out-Null
}

function Ask-YesNo {
    param([Parameter(Mandatory)][string]$Message)
    return [System.Windows.MessageBox]::Show(
        $Message,
        "piper-mat",
        "YesNo",
        "Question"
    ) -eq "Yes"
}

function Refresh-ProcessPath {
    $MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$MachinePath;$UserPath"
}

function Find-CompatiblePython {
    $PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($PyLauncher) {
        & $PyLauncher.Source -3.11 -c "import sys; assert sys.version_info >= (3, 11)" 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) {
            return [PSCustomObject]@{
                Executable = $PyLauncher.Source
                Prefix = @("-3.11")
            }
        }
    }

    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        & $PythonCommand.Source -c "import sys; assert sys.version_info >= (3, 11)" 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) {
            return [PSCustomObject]@{
                Executable = $PythonCommand.Source
                Prefix = @()
            }
        }
    }

    return $null
}

function Install-WithWinget {
    param(
        [Parameter(Mandatory)][string]$PackageId,
        [Parameter(Mandatory)]$WingetCommand
    )

    & $WingetCommand.Source install `
        --id $PackageId `
        -e `
        --source winget `
        --accept-package-agreements `
        --accept-source-agreements
    return $LASTEXITCODE -eq 0
}

$Gui = Join-Path $PSScriptRoot "windows_setup_gui.py"
if (-not (Test-Path $Gui -PathType Leaf)) {
    Show-ErrorMessage "Nie znaleziono pliku kreatora: $Gui"
    exit 2
}

$Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
$Python = Find-CompatiblePython
if (-not $Python) {
    $CanInstallPython = $Winget -and (Ask-YesNo (
        "Nie znaleziono Python 3.11 lub nowszego. " +
        "Czy zainstalować Python 3.11 automatycznie przez winget?"
    ))

    if ($CanInstallPython) {
        if (-not (Install-WithWinget -PackageId "Python.Python.3.11" -WingetCommand $Winget)) {
            Show-ErrorMessage "Automatyczna instalacja Python 3.11 nie powiodła się."
            exit 2
        }
        Refresh-ProcessPath
        Show-Info "Python został zainstalowany. Uruchom START_PIPER_MAT_GUI.bat ponownie."
        exit 0
    }

    Show-ErrorMessage (
        "Potrzebny jest Python 3.11 lub nowszy. " +
        "Zainstaluj go i uruchom starter ponownie."
    )
    exit 2
}

$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $GitCommand) {
    $CanInstallGit = $Winget -and (Ask-YesNo (
        "Nie znaleziono Git for Windows. " +
        "Czy zainstalować go automatycznie przez winget?"
    ))

    if ($CanInstallGit) {
        if (-not (Install-WithWinget -PackageId "Git.Git" -WingetCommand $Winget)) {
            Show-ErrorMessage "Automatyczna instalacja Git for Windows nie powiodła się."
            exit 2
        }
        Refresh-ProcessPath
        Show-Info "Git został zainstalowany. Uruchom START_PIPER_MAT_GUI.bat ponownie."
        exit 0
    }

    Show-ErrorMessage "Potrzebny jest Git for Windows."
    exit 2
}

& $GitCommand.Source lfs version 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    $CanInstallLfs = $Winget -and (Ask-YesNo (
        "Git działa, ale brakuje Git LFS potrzebnego do dużych plików. " +
        "Czy zainstalować Git LFS automatycznie?"
    ))

    if ($CanInstallLfs) {
        if (-not (Install-WithWinget -PackageId "GitHub.GitLFS" -WingetCommand $Winget)) {
            Show-ErrorMessage "Automatyczna instalacja Git LFS nie powiodła się."
            exit 2
        }
        Refresh-ProcessPath
        $GitCommand = Get-Command git.exe -ErrorAction Stop
        & $GitCommand.Source lfs install 1>$null 2>$null
        if ($LASTEXITCODE -ne 0) {
            Show-ErrorMessage "Git LFS został zainstalowany, ale jego inicjalizacja nie powiodła się."
            exit 2
        }
    }
}

$Arguments = @($Python.Prefix) + @($Gui)
& $Python.Executable @Arguments
exit $LASTEXITCODE
