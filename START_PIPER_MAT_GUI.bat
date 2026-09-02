@echo off
setlocal
cd /d "%~dp0"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\start_windows_gui.ps1"
set "PIPER_MAT_EXIT_CODE=%ERRORLEVEL%"

if not "%PIPER_MAT_EXIT_CODE%"=="0" (
  echo.
  echo Nie udalo sie uruchomic kreatora.
  echo Przeczytaj komunikat powyzej.
  echo.
  pause
)

exit /b %PIPER_MAT_EXIT_CODE%
