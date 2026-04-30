@echo off
REM AI Detection System v4.0 - Docker Deployment
REM Double-click to launch full stack with Docker

title AI Detection System v4.0 - Docker
color 0C

echo.
echo ========================================
echo   AI Detection System v4.0
echo   Docker Full Stack Deployment
echo ========================================
echo.

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed!
    echo Download Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo After installation, run this file again
    pause
    exit /b 1
)

echo Docker found: 
docker --version
echo.

echo Starting Docker containers...
echo.

docker-compose up -d

if errorlevel 1 (
    echo ERROR: Failed to start Docker containers
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Services are running!
echo ========================================
echo.
echo API Server:     http://localhost:8000
echo API Docs:       http://localhost:8000/docs
echo Streamlit UI:   http://localhost:8501
echo PostgreSQL:     localhost:5432
echo Redis Cache:    localhost:6379
echo.
echo To stop: docker-compose down
echo To view logs: docker-compose logs -f
echo.

pause
