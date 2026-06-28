@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0update_from_github.ps1"
if errorlevel 1 (
  echo.
  echo Update failed. Review the error above.
  pause
  exit /b 1
)
pause
