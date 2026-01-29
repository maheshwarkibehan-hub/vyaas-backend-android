@echo off
echo ============================================
echo   VYAAS AI - Desktop App Builder
echo ============================================
echo.

cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if pywebview is installed
pip show pywebview >nul 2>&1
if errorlevel 1 (
    echo Installing pywebview...
    pip install pywebview
)

REM Check if pyinstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo Installing pyinstaller...
    pip install pyinstaller
)

echo.
echo Step 1: Building Frontend...
echo ============================================
cd ..\Frontend
call pnpm build
if errorlevel 1 (
    echo Frontend build failed!
    timeout /t 5
    exit /b 1
)

echo.
echo Step 2: Creating Desktop EXE...
echo ============================================
cd ..\Backend

REM Create dist folder structure
if not exist "dist\VyaasAI" mkdir dist\VyaasAI
if not exist "dist\VyaasAI\frontend" mkdir dist\VyaasAI\frontend

REM Copy frontend files
echo Copying frontend files...
xcopy /E /Y /I "..\Frontend\out" "dist\VyaasAI\frontend"

REM Copy backend assets
echo Copying backend assets...
copy /Y ".env" "dist\VyaasAI\.env"

REM Build Desktop Bridge (Standalone EXE for cloud mode)
echo Building Desktop Bridge EXE...
pyinstaller --noconfirm ^
    --name "vyaas_desktop_bridge" ^
    --windowed ^
    --onefile ^
    --hidden-import "livekit" ^
    --hidden-import "pyautogui" ^
    --hidden-import "pyperclip" ^
    --distpath "dist\VyaasAI" ^
    vyaas_desktop_bridge.py

REM Build Main Launcher with PyInstaller
echo Building Setup/Launcher EXE...
pyinstaller --noconfirm ^
    --name "VyaasAI" ^
    --icon "..\Frontend\public\icons\favicon.ico" ^
    --windowed ^
    --onedir ^
    --add-data "..\Frontend\out;frontend" ^
    --add-data ".env;." ^
    --hidden-import "webview" ^
    --hidden-import "webview.platforms.winforms" ^
    --hidden-import "clr_loader" ^
    --hidden-import "pythonnet" ^
    desktop_launcher.py

if errorlevel 1 (
    echo PyInstaller build failed!
    timeout /t 5
    exit /b 1
)

echo.
echo ============================================
echo   BUILD COMPLETE!
echo ============================================
echo.
echo Output: Backend\dist\VyaasAI\VyaasAI.exe
echo.
echo To run: double-click VyaasAI.exe
echo.
timeout /t 5
