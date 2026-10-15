@echo off
setlocal enabledelayedexpansion
title NexusFlow AI - Shutdown Utility

echo ========================================================
echo       NexusFlow AI - Clean Shutdown Utility
echo ========================================================

echo Finding active NexusFlow processes on ports 8000 and 3000...

:: Find and terminate process on port 8000 (Backend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":8000 .*LISTENING"') do (
    echo Terminating Backend process (PID: %%a)...
    taskkill /F /PID %%a >nul 2>nul
)

:: Find and terminate process on port 3000 (Frontend)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /R /C:":3000 .*LISTENING"') do (
    echo Terminating Frontend process (PID: %%a)...
    taskkill /F /PID %%a >nul 2>nul
)

echo.
echo Shutdown complete. Ports 8000 and 3000 are freed.
echo All user files, databases, and artifacts remain intact.
echo.
pause
