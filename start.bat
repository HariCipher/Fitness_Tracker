@echo off
echo ================================
echo   IronLog - Gym Tracker Setup
echo ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please download Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/4] Python found!

:: Create virtual environment
echo [2/4] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Failed to create venv
    pause
    exit /b 1
)

:: Activate and install
echo [3/4] Installing Flask...
call venv\Scripts\activate.bat
pip install flask werkzeug

echo [4/4] Starting IronLog...
echo.
echo ================================
echo   Open: http://127.0.0.1:5000
echo   Demo login: demo / demo123
echo ================================
echo.
python app.py
pause
