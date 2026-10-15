@echo off
setlocal enabledelayedexpansion
title NexusFlow AI - Full Platform Launcher

echo ======================================================================
echo              NEXUSFLOW AI — ENTERPRISE LOCAL PLATFORM
echo ======================================================================
echo Current Directory: %~dp0
echo.

:: 1. Check Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.11+ is required but was not found on system PATH.
    pause
    exit /b 1
)

:: 2. Check Node / npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js / npm is required but was not found on system PATH.
    pause
    exit /b 1
)

:: 3. Run Pre-flight Health Check
echo [*] Executing Pre-Launch Diagnostic Health Check...
python "%~dp0health_check.py"
if %errorlevel% neq 0 (
    echo [WARNING] Some pre-flight checks indicated potential environment issues.
    echo Press any key to continue launch anyway, or Ctrl+C to abort...
    pause >nul
)

:: 4. Start Backend Service if not already running
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Backend is already running on port 8000.
) else (
    echo [*] Launching Backend Service in separate console window...
    start "NexusFlow Backend" cmd /k "call \"%~dp0start_backend.bat\""
)

:: 5. Wait for backend health readiness
echo [*] Waiting for Backend API readiness (http://127.0.0.1:8000/health)...
set /a attempts=0
:wait_backend
set /a attempts+=1
curl -s http://127.0.0.1:8000/health >nul 2>nul
if %errorlevel% equ 0 (
    echo [OK] Backend API is ONLINE and HEALTHY.
    goto backend_ready
)
if %attempts% geq 20 (
    echo [WARNING] Backend did not respond within 20 seconds. Proceeding with frontend launch...
    goto backend_ready
)
timeout /t 1 /nobreak >nul
goto wait_backend

:backend_ready

:: 6. Start Frontend (Dev or Prod)
netstat -ano | findstr /R /C:":3000 .*LISTENING" >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Frontend is already running on port 3000.
) else (
    echo [*] Launching Frontend Web UI in separate console window...
    start "NexusFlow Frontend" cmd /k "call \"%~dp0start_frontend.bat\""
)

echo.
echo ======================================================================
echo              NEXUSFLOW AI IS READY FOR DEMONSTRATION
echo ======================================================================
echo  Web Dashboard : http://localhost:3000
echo  API Docs      : http://127.0.0.1:8000/docs
echo  Health Status : http://127.0.0.1:8000/health
echo ======================================================================
echo.
echo To cleanly stop all services, run: stop_nexusflow.bat
echo.
