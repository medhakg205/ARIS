@echo off
title ARIS Studio - Arduino Runtime Intelligence System
color 0b
echo ==============================================================================
echo    ARIS STUDIO - Adaptive Runtime Intelligence System for Embedded Devices
echo ==============================================================================
echo.
echo Launching ARIS Desktop with Managed Analytical Backend...
cd /d "%~dp0aris_desktop"
call npx electron .

echo.
echo ARIS Studio session finished.
pause
