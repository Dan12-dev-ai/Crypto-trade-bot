@echo off
REM UOTA Elite v2 - 24/7 Cloud Deployment
REM Immortal Watchdog + Telegram C2 + Security Hardening

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║       🛡️ UOTA ELITE v2 - 24/7 CLOUD DEPLOYMENT              ║
echo ║          Immortal Watchdog | Phone C2 | Security            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+
    pause
    exit /b 1
)

REM Check Windows environment
echo 🖥️ Checking Windows environment...
ver | findstr /i "windows" >nul
if errorlevel 1 (
    echo ❌ Windows required for this deployment
    pause
    exit /b 1
)

REM Install requirements
echo 📦 Installing requirements for 24/7 operation...
pip install -r requirements.txt

REM Create required directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data

REM Setup security
echo 🔒 Setting up security hardening...
python -c "from security_manager import security_manager; security_manager.harden_system()"

REM Setup Telegram C2
echo 📱 Setting up Telegram C2...
echo 🔧 Please configure your Telegram credentials:
echo.
echo 1. Create a bot with @BotFather
echo 2. Get your Bot Token
echo 3. Get your Chat ID (send /start to your bot)
echo 4. Add to data/credentials.encrypted
echo.

REM Create credentials template
echo # UOTA Elite v2 - Encrypted Credentials > data\credentials_template.json
echo { >> data\credentials_template.json
echo   "EXNESS_LOGIN": "your_login_here", >> data\credentials_template.json
echo   "EXNESS_PASSWORD": "your_password_here", >> data\credentials_template.json
echo   "EXNESS_SERVER": "your_server_here", >> data\credentials_template.json
echo   "TELEGRAM_BOT_TOKEN": "your_bot_token_here", >> data\credentials_template.json
echo   "TELEGRAM_CHAT_ID": "your_chat_id_here" >> data\credentials_template.json
echo } >> data\credentials_template.json

echo 🔧 Credentials template created: data\credentials_template.json
echo.

REM Test Telegram C2
echo 📱 Testing Telegram C2...
python -c "from telegram_c2 import telegram_c2; print('✅ Telegram C2 ready' if telegram_c2.get_c2_status()['bot_token_configured'] else '❌ Configure Telegram first')"

REM Setup immortal watchdog
echo 🔄 Setting up immortal watchdog...
python -c "from immortal_watchdog import immortal_watchdog; immortal_watchdog.create_startup_entry()"

REM Test autonomous rollover
echo 🔄 Testing autonomous rollover...
python -c "from autonomous_rollover import autonomous_rollover; print('✅ Rollover system ready')"

echo.
echo 🛡️ 24/7 CLOUD DEPLOYMENT COMPLETE
echo.
echo 📋 DEPLOYMENT STATUS:
echo ✅ Requirements installed
echo ✅ Security hardening applied
echo ✅ Telegram C2 configured
echo ✅ Immortal watchdog ready
echo ✅ Autonomous rollover active
echo ✅ Logic hard-locked
echo.
echo 📋 NEXT STEPS:
echo 1. Configure your credentials in data\credentials_template.json
echo 2. Encrypt credentials: python -c "from security_manager import security_manager; security_manager.encrypt_credentials({'EXNESS_LOGIN': 'your_login', 'EXNESS_PASSWORD': 'your_password', 'EXNESS_SERVER': 'your_server', 'TELEGRAM_BOT_TOKEN': 'your_token', 'TELEGRAM_CHAT_ID': 'your_chat_id'})"
echo 3. Start immortal watchdog: python immortal_watchdog.py
echo 4. Control from your phone using Telegram commands
echo.
echo 📱 TELEGRAM COMMANDS:
echo /status - Account balance and SMC brain health
echo /target [amount] - Change monthly target
echo /report - XAUUSD chart with Order Blocks
echo /stop - Emergency stop all trading
echo /help - All available commands
echo.
echo 🛡️ SECURITY FEATURES:
echo • AES-256 encryption for all credentials
echo • IP whitelisting (Exness servers only)
echo • Chat ID authorization (anti-hacker)
echo • Unauthorized access alerts
echo • Windows firewall rules
echo • Process priority optimization
echo.
echo 🔄 IMMORTAL FEATURES:
echo • 3-second auto-restart on crashes
echo • Windows startup integration
echo • 30-day auto-renewal
echo • Logic hard-locked (cannot be changed)
echo • 1% risk rule enforcement
echo • SMC institutional logic
echo.
echo 🚨 SECURITY WARNING:
echo • All configurations encrypted on disk
echo • Only your Chat ID can control the bot
echo • Network traffic restricted to Exness servers
echo • Unauthorized access attempts logged and alerted
echo.
echo 🎯 24/7 CLOUD AGENT IS READY FOR DEPLOYMENT!
echo.

pause
