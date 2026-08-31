$ErrorActionPreference = "Stop"
Add-Type -AssemblyName PresentationFramework

function ShowInfo([string]$Message) {
    [System.Windows.MessageBox]::Show($Message, "piper-mat", "OK", "Information") | Out-Null
}

function ShowError([string]$Message) {
    [System.Windows.MessageBox]::Show($Message, "piper-mat", "OK", "Error") | Out-Null
}

function AskYesNo([string]$Message) {
    $Result = [System.Windows.MessageBox]::Show($Message, "piper-mat", "YesNo", "Question")
    return $Result -eq "Yes"
}

$Gui = Join-Path $PSScriptRoot "windows_setup_gui.py"
if (-not (Test-Path $Gui)) {
    ShowError "Nie znaleziono pliku kreatora: $Gui"
    exit 2
}

$PythonExe = $null
$PythonPrefix = @()

$PyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
if ($PyLauncher) {
    & $PyLauncher.Source -3.11 -c "import sys; print(sys.version)" 1>$null 2>$null
    if ($LASTEXITCODE -eq 0) {
        $PythonExe = $PyLauncher.Source
        $PythonPrefix = @("-3.11")
    }
}

if (-not $PythonExe) {
    $PythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($PythonCommand) {
        & $PythonCommand.Source -c "import sys; assert sys.version_info >= (3, 11)" 1>$null 2>$null
        if ($LASTEXITCODE -eq 0) {
            $PythonExe = $PythonCommand.Source
        }
    }
}

if (-not $PythonExe) {
    $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($Winget -and (AskYesNo "Nie znaleziono Python 3.11. Czy zainstalowac go automatycznie przez winget?")) {
        & $Winget.Source install --id Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements
        ShowInfo "Po instalacji uruchom ponownie START_PIPER_MAT_GUI.bat."
        exit 0
    }
    ShowError "Potrzebny jest Python 3.11 lub nowszy. Zainstaluj Python i uruchom starter ponownie."
    exit 2
}

$GitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if (-not $GitCommand) {
    $Winget = Get-Command winget.exe -ErrorAction SilentlyContinue
    if ($Winget -and (AskYesNo "Nie znaleziono Git for Windows. Czy zainstalowac go automatycznie przez winget?")) {
        & $Winget.Source install --id Git.Git -e --accept-package-agreements --accept-source-agreements
        ShowInfo "Po instalacji uruchom ponownie START_PIPER_MAT_GUI.bat."
        exit 0
    }
    ShowError "Potrzebny jest Git for Windows. Zainstaluj Git i uruchom starter ponownie."
    exit 2
}

$Arguments = @()
$Arguments += $PythonPrefix
$Arguments += $Gui
& $PythonExe @Arguments
exit $LASTEXITCODE
