#!/bin/bash

# UOTA Elite v2 - Autonomous Commander Launcher
# Elite trading system with zero-downtime infrastructure

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║          🧠 UOTA ELITE v2 - AUTONOMOUS COMMANDER              ║"
echo "║              Zero-Downtime Trading Intelligence                ║"
echo "╚══════════════════════════════════════════════════════════════╝"

# Check Python version
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8+ required. Found: $python_version"
    exit 1
fi

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "⚠️  Ollama not detected. Starting Ollama..."
    ollama serve &
    sleep 5
else
    echo "✅ Ollama is running"
fi

# Check if required model is available
if ! ollama list | grep -q "qwen2.5:32b"; then
    echo "📥 Downloading required AI model (qwen2.5:32b)..."
    ollama pull qwen2.5:32b
else
    echo "✅ AI model available"
fi

# Create necessary directories
mkdir -p logs data data/backup config

# Check environment variables
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys"
    echo "💡 For safety testing, you can use demo/testnet keys"
fi

# Check dependencies
echo "🔍 Checking dependencies..."
if ! python3 -c "import aiohttp, asyncio, pandas, numpy" 2>/dev/null; then
    echo "📦 Installing missing dependencies..."
    pip3 install -r requirements.txt
else
    echo "✅ Dependencies satisfied"
fi

# System optimization for HP i5
echo "⚡ Optimizing for HP i5 performance..."
# Set process priority (if possible)
if command -v renice &> /dev/null; then
    renice -n -10 $$ > /dev/null 2>&1
fi

# Check available memory
available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
required_memory=2048  # 2GB minimum

if [ "$available_memory" -lt "$required_memory" ]; then
    echo "⚠️  Low memory detected: ${available_memory}MB available (recommended: ${required_memory}MB+)"
    echo "💡 Consider closing other applications for optimal performance"
fi

# Menu for launch options
echo ""
echo "🚀 LAUNCH OPTIONS"
echo "═══════════════════════════════════════════════════════════════"
echo "1) 🧠 Autonomous Commander (Terminal Interface)"
echo "2) 📊 Dashboard + Commander (Browser + Terminal)"
echo "3) 🧪 Future-Proof Tests Only"
echo "4) 🎯 Black Swan Stress Tests"
echo "5) 📈 Paper Trading Mode"
echo "6) 🛡️  Demo Mode (Safe Testing)"
echo "7) 🔥 ELITE SCALE MISSION - $500→$4000"
echo ""
read -p "Select launch option [1-7]: " choice

case $choice in
    1)
        echo "🧠 Launching Autonomous Commander Terminal Interface..."
        python3 terminal_interface.py
        ;;
    2)
        echo "📊 Launching Dashboard + Commander..."
        # Start dashboard in background
        streamlit run dashboard.py --server.port 8501 --server.headless true &
        DASHBOARD_PID=$!
        
        # Start terminal interface
        echo "📊 Dashboard available at: http://localhost:8501"
        echo "🧠 Starting Commander Terminal..."
        sleep 2
        python3 terminal_interface.py
        
        # Cleanup dashboard on exit
        kill $DASHBOARD_PID 2>/dev/null
        ;;
    3)
        echo "🧪 Running Future-Proof Integration Tests..."
        python3 future_proof_tests.py
        ;;
    4)
        echo "🎯 Running Black Swan Stress Tests..."
        python3 black_swan_tests.py
        ;;
    5)
        echo "📈 Starting Paper Trading Mode..."
        python3 main.py --paper --balance 1000 --dashboard --goal "grow my account to $2000 in 30 days"
        ;;
    6)
        echo "🛡️  Starting Demo Mode (Safe Testing)..."
        echo "💰 All trading uses simulated data - No real money at risk"
        python3 main.py --paper --balance 5000 --dashboard --goal "test elite features with $5000 target in 60 days"
        ;;
    7)
        echo "🔥 LAUNCHING ELITE SCALE MISSION..."
        echo "🎯 Objective: Scale $500 → $4000 in 30 days"
        echo "🛡️  Demo Mode: All trading simulated for safety"
        python3 elite_scale_mission.py
        ;;
    *)
        echo "❌ Invalid choice. Defaulting to Autonomous Commander..."
        python3 terminal_interface.py
        ;;
esac

echo ""
echo "✅ UOTA Elite v2 session completed"
echo "📊 Logs available in: logs/"
echo "💾 Data saved in: data/"
echo "🔐 Remember: Always start with demo mode for safety testing"
