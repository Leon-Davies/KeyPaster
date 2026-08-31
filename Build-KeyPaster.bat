@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  call Run-KeyPaster.bat
  timeout /t 1 >nul
)

".venv\Scripts\python.exe" -m pip install "pyinstaller>=6.11,<7" || exit /b 1
".venv\Scripts\pyinstaller.exe" --noconfirm --clean --onefile --windowed --name KeyPaster keypaster_app.py || exit /b 1

echo.
echo Built: %CD%\dist\KeyPaster.exe
pause
