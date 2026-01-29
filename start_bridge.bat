@echo off
title VYAAS Desktop Bridge
echo ========================================
echo   VYAAS AI Desktop Bridge
echo   Connecting to cloud AI agent...
echo ========================================
echo.

cd /d "%~dp0"

REM Check if venv exists
if exist "venv\Scripts\python.exe" (
    echo Using virtual environment...
    call venv\Scripts\activate
    python vyaas_desktop_bridge.py
) else (
    echo Using system Python...
    python vyaas_desktop_bridge.py
)

pause
