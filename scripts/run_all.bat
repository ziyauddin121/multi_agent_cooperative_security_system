@echo off
REM =====================================================================
REM MACSS — Multi-Agent Cooperative Security System
REM Automated Launcher & Verification Script (Windows CMD/PowerShell)
REM =====================================================================

echo [1/4] Checking Docker daemon status...
docker info >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop first.
    exit /b 1
)

echo [2/4] Deploying all 10 MACSS containers with Docker Compose...
docker compose up -d --build

echo [3/4] Waiting 15 seconds for services to initialize...
timeout /t 15 /nobreak >nul

echo [4/4] Verifying health and running test benchmark...
curl -s http://127.0.0.1:8000/api/health
echo.
echo =====================================================================
echo  MACSS System is LIVE!
echo  - Frontend Research Dashboard : http://localhost:3000
echo  - Backend REST API & Swagger  : http://localhost:8000/docs
echo  - Live WebSocket Stream       : ws://localhost:8000/ws
echo =====================================================================
pause
