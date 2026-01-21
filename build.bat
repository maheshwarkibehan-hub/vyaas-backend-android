@echo off
echo ===================================================
echo   VYAAS AI - BACKEND BUILDER (EXE CONVERTER)
echo ===================================================

cd /d "%~dp0"

echo [1/4] Activating Virtual Environment...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Error: Virtual environment not found! Run setup first.
    pause
    exit /b
)

echo [2/4] Installing PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo Error: Failed to install PyInstaller.
    pause
    exit /b
)

echo [3/4] Building Vyaas AI EXE...
echo This may take a few minutes...

:: Build Command
:: --onefile: Bundle everything into one .exe
:: --name: Name of the output file
:: --hidden-import: Explicitly import LiveKit plugins that dynamic loaders might miss
:: --add-data: Include .env file (if you want it embedded, otherwise keep external)
:: Note: We keep .env external usually so user can edit it.

pyinstaller --noconfirm --onefile --console --name "VyaasAI_Brain" ^
    --hidden-import=livekit.plugins.google ^
    --hidden-import=livekit.agents ^
    --hidden-import=google.generativeai ^
    --hidden-import=engineio.async_drivers.aiohttp ^
    agent.py

if %errorlevel% neq 0 (
    echo Error: Build failed!
    pause
    exit /b
)

echo.
echo ===================================================
echo   BUILD SUCCESSFUL!
echo ===================================================
echo.
echo Your Vyaas AI Executable is ready at:
echo   Backend\dist\VyaasAI_Brain.exe
echo.
echo IMPORTANT: 
echo 1. Keep your '.env' file in the SAME folder as the .exe
echo    when running it on a new PC.
echo 2. Run the .exe as Administrator for System Controls.
echo.
pause
