@echo off
REM UOTA Elite v2 - Working Deployment
REM Minimal working version

echo.
echo ╔═══════════════════════════════════════
echo ║       🚀 UOTA ELITE v2 - WORKING VERSION       ║
echo ║          Minimal System | Cloud Ready              ║
echo ╚═══════════════════════════════════════
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found
    pause
    exit /b 1
)

REM Create directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data

REM Start minimal controller
echo 🚀 Starting minimal controller...
python minimal_master_controller.py

echo.
echo ✅ Minimal deployment complete
echo 🎯 Your PC can now be turned off
echo 📱 Use Telegram for control
pause
