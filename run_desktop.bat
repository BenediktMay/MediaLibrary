@echo off
REM Media Library Desktop Application Launcher for Windows

setlocal

REM Prefer the Python Launcher; fall back to python on PATH
set "PY_CMD=py -3.11"
%PY_CMD% -c "import sys" >nul 2>&1
if errorlevel 1 set "PY_CMD=python"

set "VENV_DIR=.venv"
if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY_CMD% -m venv "%VENV_DIR%"
)

REM Try to install/verify dependencies (optional - continue if pip fails)
echo Checking dependencies...
"%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt -q 2>nul

REM Run the desktop app regardless of pip status
echo Starting Media Library Desktop Application...
"%VENV_DIR%\Scripts\python.exe" desktop_app.py

if errorlevel 1 (
    echo.
    echo Error starting application. Please install dependencies manually:
    echo   "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
    pause
    exit /b 1
)

pause
endlocal
