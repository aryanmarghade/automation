@echo off
setlocal enabledelayedexpansion
title NexusFlow AI - Frontend Web UI (Dev)

echo ========================================================
echo       NexusFlow AI - Starting Frontend (Dev)
echo ========================================================

:: 1. Verify Node and npm
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm / Node.js was not found on PATH!
    echo Please install Node.js v20+ from https://nodejs.org/
    pause
    exit /b 1
)

:: 2. Check for port 3000 conflict
netstat -ano | findstr /R /C:":3000 .*LISTENING" >nul 2>nul
if %errorlevel% equ 0 (
    echo [WARNING] Port 3000 is already in use!
    echo Checking if an existing frontend is running...
    curl -s http://localhost:3000 >nul 2>nul
    if %errorlevel% equ 0 (
        echo [INFO] Frontend is already active on http://localhost:3000
        exit /b 0
    ) else (
        echo [ERROR] Port 3000 is occupied by another process.
        echo Please free port 3000 before starting NexusFlow frontend.
        pause
        exit /b 1
    )
)

:: 3. Change directory to frontend
cd /d "%~dp0frontend"

echo Launching Next.js Development Server on http://localhost:3000 ...
npm run dev
