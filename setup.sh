#!/bin/bash

# Crypto trade bot - Setup Script
# Ultimate Opportunistic Trading Agent

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Starting Crypto trade bot Setup...${NC}"

# Find suitable Python version (3.12 or 3.13)
PYTHON_CMD=""
if command -v python3.13 &> /dev/null; then
    PYTHON_CMD="python3.13"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
elif command -v python3 &> /dev/null; then
    # Check if python3 version is >= 3.12
    VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if [[ $(echo -e "$VERSION\n3.12" | sort -V | head -n1) == "3.12" ]]; then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}Error: Python 3.12 or higher is required but not found.${NC}"
    echo -e "Please install Python 3.12 or 3.13."
    exit 1
fi

echo -e "${GREEN}Using $PYTHON_CMD ($($PYTHON_CMD --version))${NC}"

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Warning: Docker is not installed. Containerized deployment will not be available.${NC}"
fi

# Check for Ollama
if ! command -v ollama &> /dev/null; then
    echo -e "${YELLOW}Warning: Ollama is not installed. Local LLM features require Ollama.${NC}"
    echo -e "Install it from: https://ollama.com/"
fi

# Create virtual environment
echo -e "${BLUE}📦 Creating virtual environment...${NC}"
$PYTHON_CMD -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}🐍 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo -e "${BLUE}📁 Creating data and log directories...${NC}"
mkdir -p logs data data/backup config

# Set up configuration
if [ ! -f config/.env ]; then
    echo -e "${BLUE}📝 Setting up .env file...${NC}"
    cp .env.example config/.env
    echo -e "${YELLOW}Action Required: Please edit config/.env with your API keys.${NC}"
fi

if [ ! -f config/config.json ]; then
    echo -e "${BLUE}📝 Creating default config.json...${NC}"
    # Minimal default config
    echo '{
    "trading": {
        "starting_balance": 1000.0,
        "max_leverage": 10.0,
        "max_risk_per_trade": 0.01
    },
    "agents": {
        "llm_model": "qwen2.5:32b"
    }
}' > config/config.json
fi

# Pull Ollama models if available
if command -v ollama &> /dev/null; then
    echo -e "${BLUE}🧠 Pulling recommended Ollama models...${NC}"
    ollama pull qwen2.5:32b || echo -e "${YELLOW}Warning: Could not pull model. You may need to do this manually later.${NC}"
fi

echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e ""
echo -e "${BLUE}To start the trading bot:${NC}"
echo -e "1. Activate virtual environment: ${YELLOW}source venv/bin/activate${NC}"
echo -e "2. Edit your credentials: ${YELLOW}nano config/.env${NC}"
echo -e "3. Run the bot: ${YELLOW}python main.py --dashboard --balance 1000${NC}"
echo -e ""
echo -e "${BLUE}For Docker deployment:${NC}"
echo -e "1. Run: ${YELLOW}docker-compose up -d${NC}"
echo -e ""
echo -e "${GREEN}Happy Trading! 🚀${NC}"
