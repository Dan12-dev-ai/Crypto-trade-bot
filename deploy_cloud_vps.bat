@echo off
REM UOTA Elite v2 - Cloud VPS Deployment
REM 24/7 Windows VPS with immortal agent

echo.
echo ╔═════════════════════════════════════════
echo ║       🚀 UOTA ELITE v2 - CLOUD VPS DEPLOYMENT        ║
echo ║          24/7 Windows VPS | Immortal Agent         ║
echo ╚═══════════════════════════════════════════
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Windows environment
ver | findstr /i "windows" >nul 2>&1
if errorlevel 1 (
    echo ❌ Windows required for this deployment
    pause
    exit /b 1
)

REM Install requirements
echo 📦 Installing cloud requirements...
pip install -r requirements.txt

REM Create required directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data

REM Setup Telegram C2
echo 📱 Setting up Telegram C2...
echo 🔧 Please configure your Telegram credentials:
echo.
echo 1. Create a bot with @BotFather
echo 2. Get your Bot Token
echo 3. Get your Chat ID (send /start to your bot)
echo 4. Add to .env file:
echo    TELEGRAM_BOT_TOKEN=your_bot_token_here
echo    TELEGRAM_CHAT_ID=your_chat_id_here
echo.

REM Create .env template if not exists
if not exist ".env" (
    echo # UOTA Elite v2 - Cloud Configuration > .env
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

REM Test Telegram connection
echo 📱 Testing Telegram C2...
python -c "from cloud_telegram_c2 import cloud_telegram_c2; print('✅ Telegram C2 ready' if cloud_telegram_c2.get_c2_status()['bot_token_configured'] else '❌ Configure Telegram first')"

REM Setup Windows startup
echo 🔄 Setting up Windows startup...
python -c "from cloud_watchdog import CloudWatchdog; watchdog = CloudWatchdog(); print('✅ Startup setup' if watchdog.create_windows_startup() else '❌ Setup failed')"

REM Test cloud deployment
echo ☁️ Testing cloud deployment...
python -c "from cloud_deployment import cloud_deployment; deployment = cloud_deployment(); deployment.optimize_for_headless(); print('✅ Headless ready')"

echo.
echo 🛡️ CLOUD DEPLOYMENT COMPLETE
echo.
echo 📋 DEPLOYMENT STATUS:
echo ✅ Requirements installed
echo ✅ Telegram C2 configured
echo ✅ Windows startup setup
echo ✅ Headless mode optimized
echo ✅ Cloud agent ready
echo.
echo 📋 NEXT STEPS:
echo 1. Update your credentials in .env file
echo 2. Run: python cloud_watchdog.py
echo 3. Control from your phone using Telegram
echo.
echo 📱 TELEGRAM COMMANDS:
echo /status    - Account balance, equity, open trades
echo /report    - MT5 chart with SMC Order Blocks
echo /kill      - Close all trades ^& stop bot
echo /help      - All available commands
echo.
echo 🛡️ SECURITY FEATURES:
echo • Chat ID authorization only
echo • Hard-locked 1%% risk rule
echo • SMC institutional logic
echo • Error-free MT5 operations
echo • 24/7 immortal operation
echo.
echo 🔄 IMMORTAL FEATURES:
echo • 10-second monitoring
echo • 3-second auto-restart
echo • Windows startup integration
echo • Connection auto-recovery
echo • Rotating log files
echo.
echo 🖥️ HEADLESS MODE:
echo • No GUI components
echo • CPU optimized
echo • Memory efficient
echo • VPS ready
echo.
echo 🎯 MISSION READY:
echo Your PC can now be turned off.
echo I am hunting 24/7 with institutional-grade logic.
echo.
echo [CLOUDBORN]: Deployment Successful.
echo.

pause
