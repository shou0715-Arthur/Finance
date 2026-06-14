@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" AI-stock.py
) else (
  python AI-stock.py
)
pause
