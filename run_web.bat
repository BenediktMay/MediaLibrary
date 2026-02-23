@echo off
REM Media Library Web Application Launcher

echo ========================================
echo    Media Library - Web Application
echo ========================================
echo.
echo Starting Flask server...
echo.
echo Once started, the application will be available at:
echo   http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Start Flask with the virtual environment
call .venv\Scripts\activate.bat
python app.py

pause
