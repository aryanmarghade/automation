@echo off
setlocal enabledelayedexpansion
title NexusFlow AI - Backend Service

echo ========================================================
echo       NexusFlow AI - Starting Backend Service
echo ========================================================

:: 1. Verify Python availability
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found on PATH!
    echo Please install Python 3.11+ from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Check for port 8000 conflict
netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul 2>nul
if %errorlevel% equ 0 (
    echo [WARNING] Port 8000 is already in use!
    echo Checking if an existing NexusFlow backend is running...
    curl -s http://127.0.0.1:8000/health >nul 2>nul
    if %errorlevel% equ 0 (
        echo [INFO] Backend is already active and healthy on port 8000.
        exit /b 0
    ) else (
        echo [ERROR] Port 8000 is occupied by another process.
        echo Please free port 8000 before starting NexusFlow backend.
        pause
        exit /b 1
    )
)

:: 3. Change directory to backend root
cd /d "%~dp0backend"

echo Launching Uvicorn ASGI server on http://127.0.0.1:8000 ...
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
