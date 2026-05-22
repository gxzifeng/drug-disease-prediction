@echo off
setlocal

echo ===================================================
echo Starting Drug-Disease Prediction System
echo ===================================================

echo [1/5] Checking Docker connection...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Cannot connect to Docker Daemon.
    echo Please make sure Docker Desktop is installed and RUNNING.
    pause
    exit /b 1
)
echo Docker is running.

echo.
echo [2/5] Checking configuration...
type backend\requirements.txt | findstr "pytest"

echo.
echo [3/5] Building and starting services...
echo This process will:
echo  1. Build backend and frontend images (using cached layers if available)
echo  2. Start MySQL, Redis, Backend, Frontend, and Celery services
echo.
echo Please wait...
docker-compose up -d --build

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to start Docker services.
    echo You can try running: docker-compose logs backend
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [4/5] Waiting for services to initialize (15s)...
timeout /t 15 >nul

echo.
echo [5/5] Opening application in browser...
start http://localhost:5173
start http://localhost:8000/docs

echo.
echo ===================================================
echo System is running!
echo Frontend: //localhttp:host:5173
echo Backend API: http://localhost:8000/docs
echo.
echo To stop the system, run: docker-compose down
echo ===================================================
echo.
echo Press any key to check container status...
pause >nul
docker-compose ps
pause
