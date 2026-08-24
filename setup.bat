@echo off
echo ======================================================================
echo   PHANTOM // Automated Setup and Launch Bootstrapper
echo ======================================================================
echo.

if not exist .env (
    if exist .env.example (
        copy .env.example .env >nul
        echo [+] Created .env configuration from .env.example
    )
)

echo [*] Checking Docker...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Docker Desktop is not running. Please start Docker Desktop and run this script again.
    pause
    exit /b 1
)

echo [*] Building and Starting PHANTOM Stack (PostgreSQL + Redis + Backend + Frontend)...
docker compose up --build -d

echo.
echo ======================================================================
echo   PHANTOM IS NOW RUNNING!
echo ======================================================================
echo   Frontend Dashboard:      http://localhost:3000
echo   Backend OpenAPI Swagger: http://localhost:8000/api/v1/docs
echo   Health Probe:            http://localhost:8000/health/live
echo   Stream Gateway Playback: http://localhost:8000/api/v1/streams/CAM-001/live.m3u8
echo ======================================================================
echo.
pause
