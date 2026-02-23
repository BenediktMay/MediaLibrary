@echo off
REM Media Library Desktop App - Clean Setup and Run

echo ========================================
echo Media Library Desktop Application Setup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo Error creating virtual environment
        echo.
        echo Alternative: Use the web version instead:
        echo   python app.py
        echo   Then open http://localhost:5000 in your browser
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Installing dependencies in virtual environment...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Error installing dependencies.
    echo.
    echo Alternative: Use the web version instead:
    echo   python app.py
    echo   Then open http://localhost:5000 in your browser
    pause
    exit /b 1
)

echo.
echo Starting Media Library Desktop Application...
echo.
python desktop_app.py

pause
