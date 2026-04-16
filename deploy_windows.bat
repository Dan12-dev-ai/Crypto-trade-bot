@echo off
REM UOTA Elite v2 - Windows Deployment Script
REM Immortal agent for 24/7 cloud operation

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║         🚀 UOTA ELITE v2 - WINDOWS DEPLOYMENT              ║
echo ║              24/7 Immortal Agent | Cloud VPS                 ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check required packages
echo 📦 Checking required packages...
python -c "import psutil, win32api, telegram" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing required packages...
    pip install psutil pywin32 python-telegram-bot
)

REM Create required directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data

REM Check .env file
if not exist ".env" (
    echo 🔧 Creating .env file...
    echo # UOTA Elite v2 - Windows Configuration > .env
    echo. >> .env
    echo # Telegram Configuration >> .env
    echo TELEGRAM_BOT_TOKEN=your_bot_token_here >> .env
    echo TELEGRAM_CHAT_ID=your_chat_id_here >> .env
    echo. >> .env
    echo # Exness MT5 Configuration >> .env
    echo EXNESS_LOGIN=your_login_here >> .env
    echo EXNESS_PASSWORD=your_password_here >> .env
    echo EXNESS_SERVER=your_server_here >> .env
    echo.
    echo 🔧 .env file created. Please update your credentials.
    pause
)

REM Test Telegram configuration
echo 📱 Testing Telegram configuration...
python -c "from telegram_notifications import telegram_notifier; print('✅ Telegram configured' if telegram_notifier.config.enabled else '❌ Telegram not configured')"

echo.
echo 🚀 DEPLOYMENT COMPLETE
echo.
echo 📋 NEXT STEPS:
echo 1. Update your credentials in .env file
echo 2. Run: python windows_master_controller.py
echo 3. Enter your target (e.g., 4000)
echo 4. Agent will run 24/7 with immortal protection
echo.
echo 🛡️ IMMORTAL FEATURES:
echo • Real-time process priority
echo • Error-free execution with auto-retry
echo • 24/7 Telegram notifications
echo • Auto-restart on crashes
echo • Windows startup integration
echo.
echo 🎯 Agent is ready for 24/7 cloud deployment!
echo.

pause
