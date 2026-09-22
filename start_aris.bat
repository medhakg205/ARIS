@echo off
title ARIS Studio - Arduino Runtime Intelligence System
color 0b
echo ==============================================================================
echo    ARIS STUDIO - Adaptive Runtime Intelligence System for Embedded Devices
echo ==============================================================================
echo.
echo [1/2] Verifying ARIS Analytical Backend (Port 8765)...
netstat -ano | findstr :8765 | findstr LISTENING >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Starting ARIS Python analytical backend...
    start "ARIS Backend Server" /min python -m uvicorn backend.api.app:app --host 127.0.0.1 --port 8765
    timeout /t 2 /nobreak >nul 2>&1
) else (
    echo ARIS analytical backend is already running on port 8765.
)

echo.
echo [2/2] Launching ARIS Desktop Application...
cd aris_desktop
npx electron .

echo.
echo ARIS Studio closed.
pause

