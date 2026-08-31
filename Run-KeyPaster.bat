@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11 or newer, or use the packaged KeyPaster.exe build from GitHub Actions.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\pythonw.exe" (
  echo First run: creating KeyPaster environment...
  py -3 -m venv .venv || exit /b 1
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || exit /b 1
)

start "" ".venv\Scripts\pythonw.exe" -m keypaster
exit /b 0
