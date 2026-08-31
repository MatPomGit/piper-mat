$ErrorActionPreference = "Stop"
Add-Type -AssemblyName PresentationFramework

function ShowInfo([string]$Message) {
    [System.Windows.MessageBox]::Show($Message, "piper-mat", "OK", "Information") | Out-Null
}
function ShowError([string]$Message) {
    [System.Windows.MessageBox]::Show($Message, "piper-mat", "OK", "Error") | Out-Null
}
function AskYesNo([string]$Message) {
    return [System.Windows.MessageBox]::Show($Message, "piper-mat", "YesNo", "Question") -eq "Yes"
}
function RefreshPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}

$Gui = Join-Path $PSScriptRoot "windows_setup_gui.py"
if (-not (Test-Path $Gui)) {
    ShowError "Nie znaleziono pliku kreatora: $Gui"
    exit 2
}

$Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
$PythonExe = $null
$PythonPrefix = @()
$PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($PyLauncher) {
    & $PyLauncher.Source -3.11 -c "import sys; assert sys.version_info >= (3, 11)" 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) { $PythonExe = $PyLauncher.Source; $PythonPrefix = @("-3.11") }
}
if (-not $PythonExe) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        & $PythonCommand.Source -c "import sys; assert sys.version_info >= (3, 11)" 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) { $PythonExe = $PythonCommand.Source }
    }
}
if (-not $PythonExe) {
    if ($Winget -and (AskYesNo "Nie znaleziono Python 3.11 lub nowszego. Czy zainstalować Python 3.11 automatycznie przez winget?")) {
        & $Winget.Source install --id Python.Python.3.11 -e --source winget --accept-package-agreements --accept-source-agreements
        RefreshPath
        ShowInfo "Python został zainstalowany. Uruchom START_PIPER_MAT_GUI.bat ponownie."
        exit 0
    }
    ShowError "Potrzebny jest Python 3.11 lub nowszy. Zainstaluj go i uruchom starter ponownie."
    exit 2
}

$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $GitCommand) {
    if ($Winget -and (AskYesNo "Nie znaleziono Git for Windows. Czy zainstalować go automatycznie przez winget?")) {
        & $Winget.Source install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
        RefreshPath
        ShowInfo "Git został zainstalowany. Uruchom START_PIPER_MAT_GUI.bat ponownie."
        exit 0
    }
    ShowError "Potrzebny jest Git for Windows."
    exit 2
}

& git lfs version 1>$null 2>$null
if ($LASTEXITCODE -ne 0) {
    if ($Winget -and (AskYesNo "Git działa, ale brakuje Git LFS potrzebnego do dużych plików. Czy zainstalować Git LFS automatycznie?")) {
        & $Winget.Source install --id GitHub.GitLFS -e --source winget --accept-package-agreements --accept-source-agreements
        RefreshPath
        & git lfs install 1>$null 2>$null
        ShowInfo "Git LFS został zainstalowany. Jeśli kreator zgłosi brak LFS, uruchom START_PIPER_MAT_GUI.bat ponownie."
    }
}

$Arguments = @(); $Arguments += $PythonPrefix; $Arguments += $Gui
& $PythonExe @Arguments
exit $LASTEXITCODE
