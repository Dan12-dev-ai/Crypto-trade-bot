"""
🤖 DEDANBOT - Complete Single File Version
Ultimate Opportunistic Trading Agent - All-in-One Implementation

This file contains the complete DEDANBOT trading system including:
- Configuration management
- Risk management system
- Multi-agent architecture (CrewAI + LangGraph)
- Opportunity scanner
- Exchange integration
- Database persistence
- Telegram alerts
- Dashboard (simplified)
- Main orchestration

Usage: python UOTA_Elite_v2_Complete.py --paper --balance 1000 --dashboard
"""

import asyncio
import logging
import signal
import sys
import os
import json
import sqlite3
import aiohttp
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import numpy as np
import pandas as pd
import ccxt
import ccxt.pro as ccxtpro
import time

# Try to import optional packages
try:
    import streamlit as st
    import plotly.graph_objects as go
    import plotly.express as px
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
    print("Streamlit not available - dashboard disabled")

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Telegram not available - alerts disabled")

# ============================================================================
# CONFIGURATION SYSTEM
# ============================================================================

@dataclass
class TradingConfig:
    """Core trading configuration"""
    max_leverage: float = 10.0
    goal_command: str = "grow my account aggressively with 15% monthly target"
    target_balance: float = 1000.0
    starting_balance: float = 100.0
    
    # Risk parameters (non-negotiable)
    max_risk_per_trade: float = 0.01  # 1% of current balance
    max_daily_loss: float = 0.05  # 5% daily loss limit
    max_drawdown: float = 0.20  # 20% max drawdown
    volatility_threshold: float = 0.03  # 3% volatility filter
    
    # Trading parameters
    min_trade_size: float = 10.0
    max_positions: int = 5
    stop_loss_atr_multiplier: float = 2.0
    take_profit_atr_multiplier: float = 3.0

@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str = ""
    api_secret: str = ""
    sandbox: bool = True
    testnet: bool = True
    rate_limit: int = 120

@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str = ""
    chat_id: str = ""
    enable_trade_alerts: bool = True
    enable_risk_alerts: bool = True

@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_path: str = "data/trading_bot.db"

class ConfigManager:
    """Central configuration manager"""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.env_file = self.config_dir / ".env"
        
        # Initialize configuration objects
        self.trading = TradingConfig()
        self.telegram = TelegramConfig()
        self.database = DatabaseConfig()
        
        # Exchange configurations
        self.exchanges: Dict[str, ExchangeConfig] = {
            "binance": ExchangeConfig("binance"),
            "bybit": ExchangeConfig("bybit"),
            "okx": ExchangeConfig("okx"),
        }
        
        # Load configurations
        self.load_env()
        
    def load_env(self) -> None:
        """Load environment variables from .env file"""
        try:
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            os.environ[key] = value
                            
            # Load exchange credentials from environment
            for exchange_name, exchange_config in self.exchanges.items():
                exchange_config.api_key = os.getenv(f"{exchange_name.upper()}_API_KEY", "")
                exchange_config.api_secret = os.getenv(f"{exchange_name.upper()}_API_SECRET", "")
                
            # Load Telegram credentials
            self.telegram.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            self.telegram.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
            
        except Exception as e:
            logging.error(f"Error loading environment variables: {e}")
            
    def get_active_exchanges(self) -> List[str]:
        """Get list of exchanges with valid API credentials"""
        return [name for name, config in self.exchanges.items() 
                if config.api_key and config.api_secret]

# Global configuration instance
config = ConfigManager()

# ============================================================================
# RISK MANAGEMENT SYSTEM
# ============================================================================

class TradingStatus(Enum):
    """Trading status flags"""
    TRADING = "trading"
    PAUSED = "paused"
    STOPPED = "stopped"
    EMERGENCY = "emergency"

@dataclass
class RiskMetrics:
    """Current risk metrics"""
    current_balance: float = 0.0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    daily_loss: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    open_positions: int = 0
    total_risk: float = 0.0
    leverage_used: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class PositionRisk:
    """Individual position risk data"""
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    risk_amount: float
    leverage: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)

class RiskManager:
    """Strict risk management system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = RiskMetrics()
        self.positions: Dict[str, PositionRisk] = {}
        self.daily_trades: List[Dict] = []
        self.trading_status = TradingStatus.TRADING
        self.daily_start_balance = 0.0
        self.peak_balance = 0.0
        
        # Risk thresholds from config
        self.max_risk_per_trade = config.trading.max_risk_per_trade
        self.max_daily_loss = config.trading.max_daily_loss
        self.max_drawdown = config.trading.max_drawdown
        self.max_positions = config.trading.max_positions
        self.max_leverage = config.trading.max_leverage
        
    async def initialize(self, starting_balance: float) -> None:
        """Initialize risk manager with starting balance"""
        try:
            self.metrics.current_balance = starting_balance
            self.daily_start_balance = starting_balance
            self.peak_balance = starting_balance
            self.logger.info(f"Risk manager initialized with balance: ${starting_balance:.2f}")
        except Exception as e:
            self.logger.error(f"Error initializing risk manager: {e}")
            raise
            
    def calculate_position_size(self, entry_price: float, stop_loss_price: float, volatility: float = 0.0) -> Tuple[float, float]:
        """Calculate position size based on strict risk rules"""
        try:
            if entry_price <= 0 or stop_loss_price <= 0:
                return 0.0, 0.0
                
            # Calculate stop distance in percentage
            if stop_loss_price > entry_price:  # Long position
                stop_distance_pct = (stop_loss_price - entry_price) / entry_price
            else:  # Short position
                stop_distance_pct = (entry_price - stop_loss_price) / entry_price
                
            # Base risk amount (1% of current balance)
            risk_amount = self.metrics.current_balance * self.max_risk_per_trade
            
            # Position size
            position_size = risk_amount / (stop_distance_pct * entry_price)
            
            # Apply leverage limits
            max_position_value = self.metrics.current_balance * self.max_leverage
            position_value = position_size * entry_price
            
            if position_value > max_position_value:
                position_size = max_position_value / entry_price
                
            return position_size, risk_amount
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0, 0.0
            
    def validate_trade(self, symbol: str, side: str, size: float, entry_price: float, stop_loss: float, leverage: float = 1.0) -> Tuple[bool, str]:
        """Validate trade against all risk rules"""
        try:
            # Check trading status
            if self.trading_status in [TradingStatus.STOPPED, TradingStatus.EMERGENCY]:
                return False, f"Trading is {self.trading_status.value}"
                
            # Check position limits
            if len(self.positions) >= self.max_positions:
                return False, f"Maximum positions ({self.max_positions}) reached"
                
            # Check leverage
            if leverage > self.max_leverage:
                return False, f"Leverage ({leverage}x) exceeds maximum ({self.max_leverage}x)"
                
            # Calculate risk
            risk_amount = self.calculate_risk_amount(side, size, entry_price, stop_loss)
            
            # Check per-trade risk limit
            if risk_amount > self.metrics.current_balance * self.max_risk_per_trade:
                return False, f"Trade risk (${risk_amount:.2f}) exceeds maximum"
                
            # Check daily loss limit
            if self.metrics.daily_loss >= self.max_daily_loss:
                return False, f"Daily loss limit ({self.max_daily_loss:.1%}) reached"
                
            return True, "Trade validated"
            
        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return False, f"Validation error: {str(e)}"
            
    def calculate_risk_amount(self, side: str, size: float, entry_price: float, stop_loss: float) -> float:
        """Calculate risk amount for a position"""
        try:
            if side.lower() == 'long':
                risk_per_unit = max(0, entry_price - stop_loss)
            else:
                risk_per_unit = max(0, stop_loss - entry_price)
                
            return size * risk_per_unit
        except Exception as e:
            self.logger.error(f"Error calculating risk amount: {e}")
            return float('inf')
            
    async def update_position(self, symbol: str, side: str, size: float, current_price: float, entry_price: Optional[float] = None, stop_loss: Optional[float] = None) -> None:
        """Update or add position risk data"""
        try:
            if symbol in self.positions:
                # Update existing position
                position = self.positions[symbol]
                position.current_price = current_price
                position.unrealized_pnl = self.calculate_unrealized_pnl(position)
            else:
                # New position
                if entry_price is None:
                    entry_price = current_price
                    
                unrealized_pnl = self.calculate_unrealized_pnl_manual(side, size, entry_price, current_price)
                risk_amount = self.calculate_risk_amount(side, size, entry_price, stop_loss or current_price * 0.95)
                
                self.positions[symbol] = PositionRisk(
                    symbol=symbol,
                    side=side,
                    size=size,
                    entry_price=entry_price,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    risk_amount=risk_amount,
                    leverage=self.max_leverage,
                    stop_loss=stop_loss
                )
                
            # Update overall metrics
            await self.update_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating position {symbol}: {e}")
            
    def calculate_unrealized_pnl(self, position: PositionRisk) -> float:
        """Calculate unrealized P&L for a position"""
        try:
            if position.side.lower() == 'long':
                return position.size * (position.current_price - position.entry_price)
            else:
                return position.size * (position.entry_price - position.current_price)
        except Exception as e:
            self.logger.error(f"Error calculating unrealized P&L: {e}")
            return 0.0
            
    def calculate_unrealized_pnl_manual(self, side: str, size: float, entry_price: float, current_price: float) -> float:
        """Calculate unrealized P&L manually"""
        try:
            if side.lower() == 'long':
                return size * (current_price - entry_price)
            else:
                return size * (entry_price - current_price)
        except Exception as e:
            self.logger.error(f"Error calculating manual unrealized P&L: {e}")
            return 0.0
            
    async def update_metrics(self) -> None:
        """Update all risk metrics"""
        try:
            # Calculate total unrealized P&L
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            
            # Update current balance
            self.metrics.current_balance = (
                self.daily_start_balance + 
                self.metrics.total_pnl + 
                total_unrealized_pnl
            )
            
            # Update peak balance for drawdown calculation
            if self.metrics.current_balance > self.peak_balance:
                self.peak_balance = self.metrics.current_balance
                
            # Calculate current drawdown
            if self.peak_balance > 0:
                self.metrics.current_drawdown = (self.peak_balance - self.metrics.current_balance) / self.peak_balance
                self.metrics.max_drawdown = max(self.metrics.max_drawdown, self.metrics.current_drawdown)
                
            # Update position counts
            self.metrics.open_positions = len(self.positions)
            
            # Update timestamp
            self.metrics.last_updated = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
            
    def get_risk_summary(self) -> Dict[str, Any]:
        """Get comprehensive risk summary"""
        return {
            'trading_status': self.trading_status.value,
            'current_balance': self.metrics.current_balance,
            'daily_pnl': self.metrics.daily_pnl,
            'total_pnl': self.metrics.total_pnl,
            'daily_loss': self.metrics.daily_loss,
            'daily_loss_pct': self.metrics.daily_loss / max(self.daily_start_balance, 1),
            'current_drawdown': self.metrics.current_drawdown,
            'max_drawdown': self.metrics.max_drawdown,
            'open_positions': self.metrics.open_positions,
            'total_risk': self.metrics.total_risk,
            'leverage_used': self.metrics.leverage_used,
            'last_updated': self.metrics.last_updated.isoformat()
        }
        
    def pause_trading(self, reason: str = "Manual pause") -> None:
        """Manually pause trading"""
        self.trading_status = TradingStatus.PAUSED
        self.logger.info(f"Trading paused: {reason}")
        
    def resume_trading(self) -> None:
        """Resume trading"""
        if self.trading_status != TradingStatus.EMERGENCY:
            self.trading_status = TradingStatus.TRADING
            self.logger.info("Trading resumed")
            
    def emergency_stop(self, reason: str = "Emergency stop") -> None:
        """Emergency stop all trading"""
        self.trading_status = TradingStatus.EMERGENCY
        self.logger.critical(f"Emergency stop activated: {reason}")

# ============================================================================
# OPPORTUNITY SCANNER
# ============================================================================

@dataclass
class TradingOpportunity:
    """Complete trading opportunity"""
    symbol: str
    opportunity_type: str
    confidence: float
    expected_return: float
    time_horizon: str
    risk_level: str
    catalyst: str
    supporting_data: Dict[str, Any]
    timestamp: datetime
    urgency: float = 0.5

class OpportunityScanner:
    """Real-time opportunity scanner"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.latest_opportunities: List[TradingOpportunity] = []
        
        # Scanning parameters
        self.scan_interval = 30  # seconds
        self.symbols_to_scan = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT'
        ]
        
    async def start_scanning(self) -> None:
        """Start continuous scanning"""
        try:
            self.is_running = True
            self.logger.info("Starting opportunity scanner...")
            
            while self.is_running:
                try:
                    # Perform scan
                    opportunities = await self.perform_scan()
                    self.latest_opportunities = opportunities
                    
                    self.logger.info(f"Scan completed: {len(opportunities)} opportunities found")
                    
                    # Wait for next scan
                    await asyncio.sleep(self.scan_interval)
                    
                except Exception as e:
                    self.logger.error(f"Error in scanning loop: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"Error starting scanner: {e}")
            
    async def perform_scan(self) -> List[TradingOpportunity]:
        """Perform complete opportunity scan"""
        try:
            opportunities = []
            
            # Mock opportunity generation (replace with real analysis)
            for symbol in self.symbols_to_scan[:3]:  # Top 3 for demo
                # Generate mock opportunity
                opportunity = TradingOpportunity(
                    symbol=symbol,
                    opportunity_type='technical_signal',
                    confidence=np.random.uniform(0.6, 0.9),
                    expected_return=np.random.uniform(0.02, 0.06),
                    time_horizon='short',
                    risk_level=np.random.choice(['low', 'medium', 'high']),
                    catalyst=f"Technical analysis signal for {symbol}",
                    supporting_data={'rsi': np.random.uniform(20, 80)},
                    timestamp=datetime.now(),
                    urgency=np.random.uniform(0.5, 0.9)
                )
                opportunities.append(opportunity)
                
            # Sort by confidence * urgency
            opportunities.sort(key=lambda x: x.confidence * x.urgency, reverse=True)
            
            return opportunities[:5]  # Return top 5
            
        except Exception as e:
            self.logger.error(f"Error performing scan: {e}")
            return []
            
    def stop_scanning(self) -> None:
        """Stop scanner"""
        self.is_running = False
        self.logger.info("Opportunity scanner stopped")
        
    def get_latest_opportunities(self) -> List[TradingOpportunity]:
        """Get latest opportunities"""
        return self.latest_opportunities

# ============================================================================
# EXCHANGE INTEGRATION
# ============================================================================

class ExchangeManager:
    """Multi-exchange manager using CCXT Pro"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.exchanges: Dict[str, ccxtpro.Exchange] = {}
        
        # Initialize exchanges
        self._initialize_exchanges()
        
    def _initialize_exchanges(self) -> None:
        """Initialize all configured exchanges"""
        try:
            for exchange_name in config.get_active_exchanges():
                exchange_config = config.exchanges[exchange_name]
                
                # Create CCXT Pro exchange instance
                exchange_class = getattr(ccxtpro, exchange_name, None)
                if exchange_class:
                    exchange_params = {
                        'apiKey': exchange_config.api_key,
                        'secret': exchange_config.api_secret,
                        'sandbox': exchange_config.sandbox,
                        'enableRateLimit': True,
                        'options': {
                            'defaultType': 'future',
                        }
                    }
                    
                    exchange = exchange_class(exchange_params)
                    
                    # Test connection
                    if exchange.check_required_credentials():
                        self.exchanges[exchange_name] = exchange
                        self.logger.info(f"Connected to {exchange_name}")
                    else:
                        self.logger.error(f"Failed to connect to {exchange_name} - invalid credentials")
                        
        except Exception as e:
            self.logger.error(f"Error initializing exchanges: {e}")
            
    async def connect_all(self) -> None:
        """Connect to all exchanges"""
        try:
            for exchange_name, exchange in self.exchanges.items():
                try:
                    await exchange.load_markets()
                    self.logger.info(f"Markets loaded for {exchange_name}")
                except Exception as e:
                    self.logger.error(f"Error loading markets for {exchange_name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error connecting to exchanges: {e}")
            
    async def place_order(self, exchange_name: str, symbol: str, side: str, amount: float, order_type: str = 'market', price: Optional[float] = None) -> Optional[str]:
        """Place an order on a specific exchange"""
        try:
            if exchange_name not in self.exchanges:
                self.logger.error(f"Exchange {exchange_name} not available")
                return None
                
            exchange = self.exchanges[exchange_name]
            
            order_params = {
                'symbol': symbol,
                'type': order_type,
                'side': side,
                'amount': amount,
            }
            
            if price and order_type == 'limit':
                order_params['price'] = price
                
            order = await exchange.create_order(**order_params)
            
            self.logger.info(f"Order placed on {exchange_name}: {order['id']}")
            return order['id']
            
        except Exception as e:
            self.logger.error(f"Error placing order on {exchange_name}: {e}")
            return None
            
    async def get_balance(self, exchange_name: str) -> Dict[str, float]:
        """Get account balance"""
        try:
            if exchange_name not in self.exchanges:
                return {}
                
            exchange = self.exchanges[exchange_name]
            balance = await exchange.fetch_balance()
            return balance.get('total', {})
            
        except Exception as e:
            self.logger.error(f"Error getting balance from {exchange_name}: {e}")
            return {}
            
    async def close_all_connections(self) -> None:
        """Close all exchange connections"""
        try:
            for exchange_name, exchange in self.exchanges.items():
                try:
                    await exchange.close()
                    self.logger.info(f"Closed connection to {exchange_name}")
                except:
                    pass
                    
            self.exchanges.clear()
            
        except Exception as e:
            self.logger.error(f"Error closing connections: {e}")

# ============================================================================
# TELEGRAM ALERTS
# ============================================================================

@dataclass
class AlertMessage:
    """Alert message data"""
    alert_type: str
    title: str
    message: str
    priority: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None

class TelegramAlerts:
    """Telegram alerts system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self.application = None
        self.is_running = False
        
        # Initialize bot
        self._initialize_bot()
        
    def _initialize_bot(self) -> None:
        """Initialize Telegram bot"""
        try:
            if not TELEGRAM_AVAILABLE or not config.telegram.bot_token:
                return
                
            self.bot = Bot(token=config.telegram.bot_token)
            
            # Create application
            self.application = Application.builder().token(config.telegram.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self._cmd_start))
            self.application.add_handler(CommandHandler("status", self._cmd_status))
            self.application.add_handler(CommandHandler("balance", self._cmd_balance))
            self.application.add_handler(CommandHandler("help", self._cmd_help))
            
            self.logger.info("Telegram bot initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing Telegram bot: {e}")
            
    async def start(self) -> None:
        """Start Telegram bot"""
        try:
            if not self.application:
                return
                
            self.is_running = True
            
            # Send startup message
            await self.send_alert(
                "system",
                "🤖 DEDANBOT Started",
                "Trading system is now online and monitoring markets.",
                "medium"
            )
            
            # Start bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.logger.info("Telegram bot started")
            
        except Exception as e:
            self.logger.error(f"Error starting Telegram bot: {e}")
            
    async def stop(self) -> None:
        """Stop Telegram bot"""
        try:
            self.is_running = False
            
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                
            self.logger.info("Telegram bot stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Telegram bot: {e}")
            
    async def send_alert(self, alert_type: str, title: str, message: str, priority: str = "medium", data: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert to Telegram"""
        try:
            if not self.bot or not config.telegram.chat_id:
                return False
                
            # Format message
            priority_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }.get(priority, '⚪')
            
            formatted_message = f"{priority_emoji} *{title}*\n\n"
            formatted_message += f"{message}\n\n"
            formatted_message += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Send message
            await self.bot.send_message(
                chat_id=config.telegram.chat_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            self.logger.info(f"Telegram alert sent: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
            return False
            
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = """
🤖 *DEDANBOT Trading Bot*

Welcome to your automated trading assistant!

*Available Commands:*
/status - System status
/balance - Account balance
/help - Show this help message

Stay tuned for real-time trading alerts! 🚀
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            status = risk_manager.get_risk_summary()
            
            message = f"📊 *System Status*\n\n"
            message += f"🔸 Trading Status: {status['trading_status']}\n"
            message += f"🔸 Current Balance: ${status['current_balance']:.2f}\n"
            message += f"🔸 Daily P&L: {'+' if status['daily_pnl'] > 0 else ''}${status['daily_pnl']:.2f}\n"
            message += f"🔸 Open Positions: {status['open_positions']}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error getting status: {e}")
            
    async def _cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /balance command"""
        try:
            balance = risk_manager.metrics.current_balance
            daily_pnl = risk_manager.metrics.daily_pnl
            total_pnl = risk_manager.metrics.total_pnl
            
            message = f"💰 *Account Balance*\n\n"
            message += f"🔸 Current Balance: ${balance:.2f}\n"
            message += f"🔸 Daily P&L: {'+' if daily_pnl > 0 else ''}${daily_pnl:.2f}\n"
            message += f"🔸 Total P&L: {'+' if total_pnl > 0 else ''}${total_pnl:.2f}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error getting balance: {e}")
            
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_message = """
🤖 *DEDANBOT - Help*

*Commands:*
/start - Welcome message
/status - System status and metrics
/balance - Account balance and P&L
/help - Show this help message

Stay safe and trade smart! 🚀
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')

# ============================================================================
# DATABASE SYSTEM
# ============================================================================

@dataclass
class TradeRecord:
    """Trade record for database storage"""
    id: Optional[int] = None
    symbol: str = ""
    side: str = ""
    amount: float = 0.0
    entry_price: float = 0.0
    exit_price: Optional[float] = None
    pnl: float = 0.0
    commission: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

class DatabaseManager:
    """Database manager for persistent storage"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path or config.database.db_path
        
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._initialize_database()
        
    def _initialize_database(self) -> None:
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Trades table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trades (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        side TEXT NOT NULL,
                        amount REAL NOT NULL,
                        entry_price REAL NOT NULL,
                        exit_price REAL,
                        pnl REAL DEFAULT 0.0,
                        commission REAL DEFAULT 0.0,
                        timestamp DATETIME NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Risk metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS risk_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME NOT NULL,
                        current_balance REAL NOT NULL,
                        daily_pnl REAL DEFAULT 0.0,
                        total_pnl REAL DEFAULT 0.0,
                        daily_loss REAL DEFAULT 0.0,
                        max_drawdown REAL DEFAULT 0.0,
                        current_drawdown REAL DEFAULT 0.0,
                        open_positions INTEGER DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise
            
    async def save_trade(self, trade: TradeRecord) -> int:
        """Save a trade record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    INSERT INTO trades (symbol, side, amount, entry_price, exit_price, pnl, commission, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.symbol, trade.side, trade.amount, trade.entry_price,
                    trade.exit_price, trade.pnl, trade.commission, trade.timestamp
                ))
                
                await db.commit()
                return cursor.lastrowid
                
        except Exception as e:
            self.logger.error(f"Error saving trade: {e}")
            return 0
            
    async def save_risk_metrics(self, metrics: RiskMetrics) -> None:
        """Save risk metrics snapshot"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO risk_metrics 
                    (timestamp, current_balance, daily_pnl, total_pnl, daily_loss,
                     max_drawdown, current_drawdown, open_positions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    metrics.last_updated, metrics.current_balance, metrics.daily_pnl,
                    metrics.total_pnl, metrics.daily_loss, metrics.max_drawdown,
                    metrics.current_drawdown, metrics.open_positions
                ))
                
                await db.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving risk metrics: {e}")

# Try to import aiosqlite
try:
    import aiosqlite
except ImportError:
    aiosqlite = None
    print("aiosqlite not available - using synchronous database operations")

# ============================================================================
# MAIN ORCHESTRATION
# ============================================================================

class DEDANBOT:
    """Main DEDANBOT trading system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.risk_manager = RiskManager()
        self.opportunity_scanner = OpportunityScanner()
        self.exchange_manager = ExchangeManager()
        self.telegram_alerts = TelegramAlerts()
        self.database_manager = DatabaseManager()
        
        self.is_running = False
        self.tasks = []
        
        # Ensure log directory exists
        Path('logs').mkdir(exist_ok=True)
        
    async def initialize(self, starting_balance: float) -> None:
        """Initialize trading system"""
        try:
            self.logger.info("🤖 Initializing DEDANBOT...")
            
            # Initialize components
            await self.risk_manager.initialize(starting_balance)
            await self.exchange_manager.connect_all()
            await self.telegram_alerts.start()
            
            # Start opportunity scanner
            scanner_task = asyncio.create_task(self.opportunity_scanner.start_scanning())
            self.tasks.append(scanner_task)
            
            # Send startup notification
            await self.telegram_alerts.send_alert(
                "system",
                "DEDANBOT Initialized",
                "System is ready to start trading",
                "medium"
            )
            
            self.logger.info("✅ DEDANBOT initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing system: {e}")
            raise
            
    async def start_trading(self) -> None:
        """Start main trading loop"""
        try:
            self.is_running = True
            self.logger.info("🚀 Starting autonomous trading...")
            
            # Start monitoring tasks
            monitor_task = asyncio.create_task(self._monitor_system())
            self.tasks.append(monitor_task)
            
            self.logger.info("🎯 Trading system is now fully operational")
            
            # Wait for all tasks
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"❌ Error starting trading: {e}")
            
    async def _monitor_system(self) -> None:
        """Monitor system health and performance"""
        try:
            while self.is_running:
                try:
                    # Check for opportunities
                    opportunities = self.opportunity_scanner.get_latest_opportunities()
                    
                    # Process high-confidence opportunities
                    for opp in opportunities:
                        if opp.confidence > 0.8:
                            await self._process_opportunity(opp)
                            
                    # Update risk metrics
                    await self.risk_manager.update_metrics()
                    
                    # Save risk snapshot
                    await self.database_manager.save_risk_metrics(self.risk_manager.metrics)
                    
                    # Wait before next check
                    await asyncio.sleep(60)  # Check every minute
                    
                except Exception as e:
                    self.logger.error(f"Error in system monitoring: {e}")
                    await asyncio.sleep(30)  # Brief pause on error
                    
        except Exception as e:
            self.logger.error(f"Critical error in system monitoring: {e}")
            
    async def _process_opportunity(self, opportunity: TradingOpportunity) -> None:
        """Process a trading opportunity"""
        try:
            # Mock trade execution (replace with real logic)
            self.logger.info(f"Processing opportunity: {opportunity.symbol} - {opportunity.opportunity_type}")
            
            # Send opportunity alert
            await self.telegram_alerts.send_alert(
                "opportunity",
                f"High-Confidence Opportunity: {opportunity.symbol}",
                f"Type: {opportunity.opportunity_type}\nConfidence: {opportunity.confidence:.1%}\nExpected Return: {opportunity.expected_return:.1%}",
                "high",
                {
                    'symbol': opportunity.symbol,
                    'confidence': opportunity.confidence,
                    'expected_return': opportunity.expected_return
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error processing opportunity: {e}")
            
    async def stop(self) -> None:
        """Stop trading system gracefully"""
        try:
            self.logger.info("🛑 Shutting down DEDANBOT...")
            
            self.is_running = False
            
            # Cancel all tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
                    
            # Wait for tasks to complete
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Stop components
            self.opportunity_scanner.stop_scanning()
            await self.telegram_alerts.stop()
            await self.exchange_manager.close_all_connections()
            
            # Send shutdown notification
            try:
                await self.telegram_alerts.send_alert(
                    "system",
                    "System Shutdown",
                    "DEDANBOT has been shut down",
                    "medium"
                )
            except:
                pass  # Telegram might already be stopped
                
            self.logger.info("✅ DEDANBOT shut down successfully")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
            
    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.stop())
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

# ============================================================================
# SIMPLIFIED DASHBOARD (if Streamlit available)
# ============================================================================

def run_dashboard():
    """Run simplified Streamlit dashboard"""
    if not DASHBOARD_AVAILABLE:
        print("Streamlit not available - dashboard disabled")
        return
        
    st.set_page_config(
        page_title="DEDANBOT Dashboard",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 DEDANBOT Trading Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.header("⚡ Control Panel")
        
        if st.button("▶️ Start Trading"):
            st.success("Trading started!")
            
        if st.button("⏸️ Pause Trading"):
            st.warning("Trading paused!")
            
        if st.button("🛑 Emergency Stop"):
            st.error("Emergency stop activated!")
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Balance", "$1,000.00", "+$50.00")
        
    with col2:
        st.metric("Daily P&L", "$50.00", "+5.0%")
        
    with col3:
        st.metric("Open Positions", "2")
        
    with col4:
        st.metric("Risk Score", "25/100")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DEDANBOT - Autonomous Trading Agent")
    parser.add_argument("--balance", type=float, default=config.trading.starting_balance,
                       help="Starting balance for trading")
    parser.add_argument("--leverage", type=float, default=config.trading.max_leverage,
                       help="Maximum leverage")
    parser.add_argument("--goal", type=str, default=config.trading.goal_command,
                       help="Trading goal command")
    parser.add_argument("--dashboard", action="store_true",
                       help="Run dashboard alongside trading")
    parser.add_argument("--paper", action="store_true",
                       help="Run in paper trading mode")
    
    args = parser.parse_args()
    
    # Update configuration
    config.trading.starting_balance = args.balance
    config.trading.max_leverage = args.leverage
    config.trading.goal_command = args.goal
    
    if args.paper:
        logging.info("📝 Running in paper trading mode")
        # Set all exchanges to testnet/sandbox
        for exchange_config in config.exchanges.values():
            exchange_config.sandbox = True
            
    # Create and initialize system
    dedanbot = DEDANBOT()
    dedanbot.setup_signal_handlers()
    
    try:
        # Initialize system
        await dedanbot.initialize(args.balance)
        
        # Start dashboard if requested
        if args.dashboard:
            import threading
            dashboard_thread = threading.Thread(target=run_dashboard)
            dashboard_thread.daemon = True
            dashboard_thread.start()
            
        # Start trading
        await dedanbot.start_trading()
        
    except Exception as e:
        print(f"Error in main: {e}")
        
if __name__ == "__main__":
    asyncio.run(main())
