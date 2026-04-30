@echo off
REM AI Detection System v4.0 - Multi-Camera + API
REM Double-click to launch multi-camera system with REST API

title AI Detection System v4.0 - Multi-Camera API
color 0B

echo.
echo ========================================
echo   AI Detection System v4.0
echo   Multi-Camera + REST API
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
pip install -q ultralytics opencv-python pillow matplotlib customtkinter numpy pandas openpyxl PyYAML fastapi uvicorn 2>nul

echo.
echo Starting Multi-Camera System...
echo.
echo API Server: http://localhost:8000
echo API Docs:   http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

python phase4_multicamera.py

pause
