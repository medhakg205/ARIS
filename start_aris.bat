@echo off
title ARIS Studio - Arduino Runtime Intelligence System
color 0b
echo ==============================================================================
echo    ARIS STUDIO - Adaptive Runtime Intelligence System for Embedded Devices
echo ==============================================================================
echo Launching ARIS Standalone Desktop Application...
cd aris_desktop
npx electron .

echo.
echo ARIS Studio closed.
pause
