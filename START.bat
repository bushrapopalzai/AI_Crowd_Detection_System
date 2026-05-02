@echo off
title AI Crowd Detection System v4.0
color 0A

echo.
echo ====================================================
echo   AI Crowd Detection System v4.0
echo ====================================================
echo.
echo   [1] GUI Dashboard  (default)
echo   [2] API Server only
echo.
set /p CHOICE="Select mode (1/2, default=1): "

if "%CHOICE%"=="2" (
    set MODE=api
) else (
    set MODE=gui
)

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://www.python.org
    pause & exit /b 1
)

echo.
echo Installing / verifying dependencies...
pip install -q -r requirements.txt

echo.
echo Starting in %MODE% mode...
echo.
python main.py --mode %MODE%

pause
