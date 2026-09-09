@echo off
title ARIS Studio - Arduino Runtime Intelligence System
color 0b
echo ==============================================================================
echo    ARIS STUDIO v2.0 - Arduino Runtime Intelligence & AI Optimization Platform
echo ==============================================================================
echo [1/2] Starting ARIS Core Python Backend on port 8765...
start /b python aris_core\api_server.py

echo [2/2] Launching ARIS Standalone Desktop Application...
cd aris_desktop
npx electron .

echo.
echo ARIS Studio closed.
pause
