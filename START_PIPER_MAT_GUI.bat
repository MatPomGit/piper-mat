@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\start_windows_gui.ps1"

if errorlevel 1 (
  echo.
  echo Nie udalo sie uruchomic kreatora.
  echo Przeczytaj komunikat powyzej.
  echo.
  pause
)
