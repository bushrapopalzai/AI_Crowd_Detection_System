@echo off
REM AI Detection System v4.0 - Analytics & Reports
REM Double-click to generate reports and analytics

title AI Detection System v4.0 - Analytics
color 0E

echo.
echo ========================================
echo   AI Detection System v4.0
echo   Analytics & Report Generator
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Install Python 3.10+ from https://www.python.org
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -q ultralytics opencv-python pillow matplotlib customtkinter numpy pandas openpyxl PyYAML 2>nul

echo.
echo Starting Analytics Engine...
echo.
echo Reports will be saved to: reports/ folder
echo.

python phase5_analytics.py

pause
