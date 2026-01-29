@echo off
title VYAAS AI - Desktop Bridge + WhatsApp Service
echo ========================================
echo   VYAAS AI - Full Local Bridge
echo   Starting WhatsApp Service and Bridge
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js is not installed!
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
)

REM Check if WhatsApp Service dependencies are installed
if not exist "whatsapp-service\node_modules" (
    echo [INFO] Installing WhatsApp Service dependencies...
    cd whatsapp-service
    call npm install
    cd ..
    echo.
)

REM Start WhatsApp Service in a new terminal
echo [1/2] Starting WhatsApp Service...
start "VYAAS WhatsApp Service" cmd /k "cd whatsapp-service && npm start"
echo       WhatsApp Service starting on http://127.0.0.1:3001

REM Wait for WhatsApp Service to start
timeout /t 5 /nobreak >nul

REM Start Desktop Bridge
echo [2/2] Starting Desktop Bridge...
echo.

if exist "venv\Scripts\python.exe" (
    echo Using virtual environment...
    call venv\Scripts\activate
    python vyaas_desktop_bridge.py
) else (
    echo Using system Python...
    python vyaas_desktop_bridge.py
)

pause
