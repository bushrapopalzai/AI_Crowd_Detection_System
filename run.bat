@echo off
REM AI Detection System v4.0 - Quick Start
REM Just double-click this file to run!

title AI Detection System v4.0
color 0A

echo.
echo ========================================
echo   AI Detection System v4.0
echo   Quick Start Launcher
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python 3.10+ from https://www.python.org
    echo Check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Checking dependencies...
pip install -q ultralytics opencv-python pillow matplotlib customtkinter numpy pandas openpyxl PyYAML 2>nul

echo.
echo Starting AI Detection System...
echo.

python main_v2.py

pause