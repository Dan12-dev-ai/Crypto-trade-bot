# 🤖 Crypto trade bot - Ultimate Opportunistic Trading Agent

A production-ready, worldwide elite autonomous AI trading agent that works on both Crypto futures and Forex with zero human intervention after initial setup.

## ✨ Core Features

### 🎯 Elite Multi-Agent Architecture
- **Goal & Risk Master Agent**: Calculates daily targets, position sizes, enforces strict risk rules
- **Market Analyst Agent**: Technical analysis + FinRL-style reinforcement learning signals  
- **Opportunity Spotter Agent**: Detects news shocks, volatility spikes, sentiment explosions, on-chain anomalies
- **Executor Agent**: Places orders with correct leverage, manages SL/TP/trailing stops
- **Supervisor Agent**: Orchestrates everything, decides when to act or pause

### ⚡ Strict Risk Engine (Non-Negotiable)
- Max risk per trade = 1% of current balance
- Max daily loss = 5% → auto pause trading
- Max drawdown = 20% → go to cash and alert user
- Position size calculated automatically using leverage + stop distance
- Volatility filter: reduce size or wait in crazy markets

### 🌍 Worldwide & Most International Features
- Support all major exchanges via CCXT: Binance, Bybit, OKX, Hyperliquid, Gate.io (crypto futures)
- Plus OANDA, IC Markets, Pepperstone (Forex)
- Multi-pair, multi-timeframe, multi-currency support
- Auto-detect "great opportunities" globally (news, X sentiment, on-chain, funding rates)

### 📊 Best Real-Time Dashboard
- Live balance & equity curve chart
- Current goal progress (percentage to target)
- Last 10 trades with P&L
- Active positions with real-time PNL
- Opportunity alerts panel
- Risk metrics (drawdown, daily loss, leverage used)
- Manual pause/resume button and emergency stop
- Settings page to change goal or leverage on the fly
- Dark mode, responsive, professional design

### 📱 Advanced Telegram Alerts
- Instant alert on every trade opened/closed (with details)
- High-profit opportunity detected
- Risk warnings (daily loss approaching limit, drawdown alert)
- Daily summary report at midnight
- Goal milestone reached (e.g. "Balance now $450 – 45% to target")
- Critical events (agent paused, error occurred, etc.)

### 🛠 Tech Stack (100% Free & Open-Source)
- Python 3.12
- CrewAI + LangGraph
- CCXT Pro
- FreqAI / TA-Lib + pandas + numpy
- Ollama (local LLM – use latest best free model like Qwen3-32B or Llama3.3-70B)
- Streamlit (for dashboard)
- python-telegram-bot
- Docker support
- Persistent SQLite database for memory and logs

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (recommended)
- Ollama installed locally (for AI agents)
- Telegram Bot Token (optional, for alerts)

### 1. Clone & Setup
```bash
git clone <repository-url>
cd Crypto-trade-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

Add your exchange API keys:
```bash
# Example for Binance
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# Example for Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 3. Start Ollama (Local LLM)
```bash
# Pull the recommended model
ollama pull qwen2.5:32b

# Start Ollama server
ollama serve
```

### 4. Run in Paper Trading Mode
```bash
# Basic paper trading
python main.py --paper --balance 1000 --dashboard

# With custom goal and leverage
python main.py --paper --balance 5000 --leverage 20 --goal "upscale 500 to 5000 in one month" --dashboard
```

### 5. Docker Deployment (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f crypto_trade_bot

# Stop
docker-compose down
```

## 📖 Detailed Setup Guide

### Exchange Setup

#### Crypto Exchanges
1. **Binance Futures**
   - Go to [Binance](https://www.binance.com)
   - Create API key with futures trading enabled
   - Add to `.env`: `BINANCE_API_KEY` and `BINANCE_API_SECRET`

2. **Bybit**
   - Go to [Bybit](https://www.bybit.com)
   - Create API key with derivatives trading
   - Add to `.env`: `BYBIT_API_KEY` and `BYBIT_API_SECRET`

3. **OKX**
   - Go to [OKX](https://www.okx.com)
   - Create API key with trading permissions
   - Add to `.env`: `OKX_API_KEY`, `OKX_API_SECRET`, `OKX_PASSPHRASE`

#### Forex Brokers
1. **OANDA**
   - Go to [OANDA](https://www.oanda.com)
   - Create API key for trading
   - Add to `.env`: `OANDA_API_KEY` and `OANDA_API_SECRET`

### Telegram Bot Setup
1. Create bot with [@BotFather](https://t.me/botfather)
2. Get bot token
3. Get your chat ID (send `/start` to your bot, check updates)
4. Add to `.env`: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`

### Ollama Setup
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull recommended models
ollama pull qwen2.5:32b
ollama pull llama3.1:8b

# Start server
ollama serve
```

## 🎮 Usage Commands

### Basic Commands
```bash
# Start with default settings
python main.py

# Paper trading mode
python main.py --paper

# With dashboard
python main.py --dashboard

# Custom parameters
python main.py --balance 10000 --leverage 15 --goal "grow my account aggressively with 20% monthly target" --dashboard

# Backtesting mode
python main.py --backtest
```

### Telegram Commands
- `/start` - Welcome message
- `/status` - System status and metrics
- `/balance` - Account balance and P&L
- `/positions` - Active positions
- `/risk` - Risk management metrics
- `/opportunities` - Current trading opportunities
- `/pause` - Pause trading
- `/resume` - Resume trading
- `/emergency` - Emergency stop all trading
- `/help` - Show all commands

## 📊 Dashboard Features

### Overview Tab
- Real-time balance and equity curve
- Daily P&L and goal progress
- Risk score and system metrics
- Recent activity feed

### Positions Tab
- Active positions with real-time P&L
- Position details (entry, size, leverage)
- Risk breakdown and distribution charts

### Opportunities Tab
- High-confidence trading opportunities
- Filter by confidence, risk level, type
- Quick trade execution buttons
- Opportunity analysis tools

### Settings Tab
- Update trading goals and leverage
- Risk management parameters
- Exchange configuration
- Manual controls (pause, emergency stop)

### Analytics Tab
- Performance statistics
- Trade distribution charts
- Risk metrics history
- Profit factor and win rate

## 🔧 Configuration

### Trading Parameters
```python
# In config.py or via command line
max_leverage = 10.0  # Maximum leverage
goal_command = "upscale 100 to 1000 in one month"
starting_balance = 100.0
target_balance = 1000.0
```

### Risk Management
```python
# Strict risk rules (non-negotiable)
max_risk_per_trade = 0.01  # 1% of current balance
max_daily_loss = 0.05  # 5% daily loss limit
max_drawdown = 0.20  # 20% max drawdown
volatility_threshold = 0.03  # 3% volatility filter
```

### Agent Settings
```python
# AI agent configuration
llm_model = "qwen2.5:32b"
ollama_base_url = "http://localhost:11434"
crewai_execution_timeout = 300  # seconds
```

## 🐳 Docker Deployment

### Development
```bash
# Build image
docker build -t crypto_trade_bot .

# Run container
docker run -d \
  --name crypto_trade_bot \
  -p 8501:8501 \
  -p 8080:8080 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/config/.env:/app/.env:ro \
  crypto_trade_bot
```

### Production with Docker Compose
```bash
# Start all services
docker-compose up -d

# Scale for high availability
docker-compose up -d --scale crypto_trade_bot=3

# Update services
docker-compose pull
docker-compose up -d
```

### Environment Variables for Docker
```yaml
# In docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  - TZ=UTC
  - OLLAMA_BASE_URL=http://ollama:11434
```

## ☁️ Cloud Deployment

### VPS Recommendations
- **DigitalOcean**: $20/month droplet (4GB RAM, 2 vCPUs)
- **Vultr**: $20/month instance (4GB RAM, 2 vCPUs)
- **Linode**: $20/month Linode (4GB RAM, 2 vCPUs)
- **AWS EC2**: t3.medium (4GB RAM, 2 vCPUs)

### Deployment Steps
```bash
# 1. Setup VPS
sudo apt update && sudo apt upgrade -y
sudo apt install docker.io docker-compose git -y

# 2. Clone repository
git clone <repository-url>
cd Crypto trade bot

# 3. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 4. Deploy
docker-compose up -d

# 5. Setup SSL (optional)
sudo certbot --nginx -d yourdomain.com
```

## 🔒 Security Best Practices

### API Key Management
- Use API keys with limited permissions (trading only, no withdrawal)
- Enable IP whitelisting if available
- Regularly rotate API keys
- Never commit API keys to version control

### System Security
- Run in Docker containers
- Use firewall (ufw/iptables)
- Enable automatic security updates
- Monitor system logs

### Trading Security
- Start with paper trading
- Use small position sizes initially
- Monitor risk metrics closely
- Set emergency stop conditions

## 📈 Performance Monitoring

### Key Metrics
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Total profit / Total loss
- **Sharpe Ratio**: Risk-adjusted returns
- **Max Drawdown**: Largest peak-to-trough decline
- **Daily P&L**: Daily profit and loss

### Monitoring Tools
- Real-time dashboard
- Telegram alerts
- Database logs
- System health checks
- Performance analytics

## 🐛 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Solution: Install missing packages
pip install -r requirements.txt

# Or install specific package
pip install ccxt pandas numpy
```

#### Connection Issues
```bash
# Check API keys
python -c "from config import config; print(config.get_active_exchanges())"

# Test exchange connection
python -c "import ccxt; print(ccxt.binance().fetch_balance())"
```

#### Ollama Issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama
pkill ollama && ollama serve
```

#### Database Issues
```bash
# Check database permissions
ls -la data/
chmod 755 data/

# Rebuild database
rm data/trading_bot.db
python main.py --paper  # Will recreate
```

### Debug Mode
```bash
# Enable debug logging
export PYTHONPATH=$(pwd)
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"

# Run with verbose output
python main.py --paper --dashboard 2>&1 | tee debug.log
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## ⚖️ Risk Warning
Trading involves significant risk. Crypto trade bot is provided as-is without any guarantees. Always start with a small balance or paper trading.

## 📄 License
MIT License. See LICENSE for details.

---

**🚀 Ready to start your autonomous trading journey with Crypto trade bot?**

Paper trading command:
```bash
python main.py --paper --balance 1000 --goal "grow my account aggressively with 15% monthly target" --dashboard
```

**Happy Trading! 📈💰**
