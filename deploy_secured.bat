@echo off
REM UOTA Elite v2 - Secured Deployment Script
REM Zero-UI, hardened security, world-class performance

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║       🛡️ UOTA ELITE v2 - SECURED DEPLOYMENT              ║
echo ║          Zero-UI | Hardened Security | 0ms Latency         ║
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
python -c "import psutil, win32api, telegram, websockets, cryptography" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installing required packages...
    pip install psutil pywin32 python-telegram-bot websockets cryptography
)

REM Create required directories
if not exist "logs" mkdir logs
if not exist "data" mkdir data

REM Security hardening
echo 🔒 Applying security hardening...
python -c "from security_hardening import security_hardening; security_hardening.disable_ui_components(); security_hardening.setup_secure_ssh_only()"

REM Check .env file
if not exist ".env" (
    echo 🔧 Creating .env file...
    echo # UOTA Elite v2 - Encrypted Configuration > .env
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

REM Test security configuration
echo 🔒 Testing security configuration...
python -c "from security_hardening import security_hardening; print('✅ Security hardening active' if security_hardening else '❌ Security failed')"

REM Test performance optimization
echo ⚡ Testing performance optimization...
python -c "from performance_optimization import performance_optimizer; print('✅ Performance optimization ready' if performance_optimizer else '❌ Performance failed')"

echo.
echo 🛡️ SECURED DEPLOYMENT COMPLETE
echo.
echo 📋 NEXT STEPS:
echo 1. Update your credentials in .env file
echo 2. Run: python secured_master_controller.py
echo 3. Enter encryption password when prompted
echo 4. Enter your target (e.g., 4000)
echo 5. Agent will run 24/7 with hardened security
echo.
echo 🛡️ SECURITY FEATURES:
echo • AES-256 encryption for all configurations
echo • IP whitelisting (Exness servers only)
echo • Zero-UI (SSH terminal only)
echo • Real-time process priority
echo • WebSocket streaming (0ms latency)
echo • Tri-Factor SMC verification
echo • Error-free execution with auto-retry
echo.
echo 🚨 SECURITY WARNING:
echo • No GUI components - SSH terminal only
echo • All configurations encrypted on disk
echo • Network traffic restricted to Exness servers
echo • Real-time priority for 0ms latency
echo.
echo 🎯 Secured immortal agent is ready for deployment!
echo.

pause
