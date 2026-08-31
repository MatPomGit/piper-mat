$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName PresentationFramework

function Show-Info([string]$message) {
    [System.Windows.MessageBox]::Show($message, 'piper-mat', 'OK', 'Information') | Out-Null
}

function Show-Error([string]$message) {
    [System.Windows.MessageBox]::Show($message, 'piper-mat', 'OK', 'Error') | Out-Null
}

function Ask-YesNo([string]$message) {
    $result = [System.Windows.MessageBox]::Show($message, 'piper-mat', 'YesNo', 'Question')
    return $result -eq 'Yes'
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$gui = Join-Path $PSScriptRoot 'windows_setup_gui.py'

if (-not (Test-Path $gui)) {
    Show-Error "Nie znaleziono pliku kreatora:`n$gui"
    exit 2
}

$python = $null
try {
    $candidate = Get-Command py.exe -ErrorAction Stop
    & $candidate.Source -3.11 -c "import sys; print(sys.version)" *> $null
    if ($LASTEXITCODE -eq 0) {
        $python = @($candidate.Source, '-3.11')
    }
} catch {}

if (-not $python) {
    try {
        $candidate = Get-Command python.exe -ErrorAction Stop
        & $candidate.Source -c "import sys; assert sys.version_info >= (3, 11)" *> $null
        if ($LASTEXITCODE -eq 0) {
            $python = @($candidate.Source)
        }
    } catch {}
}

if (-not $python) {
    if (Get-Command winget.exe -ErrorAction SilentlyContinue) {
        if (Ask-YesNo "Na komputerze nie znaleziono Pythona 3.11 lub nowszego.`n`nCzy mam spróbować zainstalować Python 3.11 automatycznie przez winget?") {
            winget install --id Python.Python.3.11 -e --accept-package-agreements --accept-source-agreements
            Show-Info "Instalacja Pythona została uruchomiona/zakończona.`n`nZamknij to okno i uruchom START_PIPER_MAT_GUI.bat ponownie."
            exit 0
        }
    }
    Show-Error "Do uruchomienia kreatora potrzebny jest Python 3.11 lub nowszy.`n`nNajprościej zainstalować go z Microsoft Store albo ze strony python.org. Podczas instalacji zaznacz opcję dodania Pythona do PATH."
    exit 2
}

if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) {
    if (Get-Command winget.exe -ErrorAction SilentlyContinue) {
        if (Ask-YesNo "Na komputerze nie znaleziono Git for Windows.`n`nCzy mam spróbować zainstalować Git automatycznie przez winget?") {
            winget install --id Git.Git -e --accept-package-agreements --accept-source-agreements
            Show-Info "Instalacja Git została uruchomiona/zakończona.`n`nZamknij to okno i uruchom START_PIPER_MAT_GUI.bat ponownie."
            exit 0
        }
    }
    Show-Error "Do pobrania projektu potrzebny jest Git for Windows.`n`nZainstaluj Git i uruchom kreator ponownie."
    exit 2
}

if ($python.Count -eq 2) {
    & $python[0] $python[1] $gui
} else {
    & $python[0] $gui
}
exit $LASTEXITCODE
