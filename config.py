"""
DEDANBOT - Configuration Management
Ultimate Opportunistic Trading Agent Configuration
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

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
    trailing_stop_activation: float = 1.5  # ATR multiplier
    
@dataclass
class ExchangeConfig:
    """Exchange configuration"""
    name: str
    api_key: str = ""
    api_secret: str = ""
    passphrase: str = ""  # For exchanges like OKX
    sandbox: bool = True
    testnet: bool = True
    rate_limit: int = 120  # requests per minute
    
@dataclass
class AgentConfig:
    """Agent configuration"""
    llm_model: str = "qwen2.5:32b"  # Local Ollama model
    ollama_base_url: str = "http://localhost:11434"
    crewai_execution_timeout: int = 300  # seconds
    max_execution_retries: int = 3
    agent_memory_size: int = 100
    
@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    host: str = "0.0.0.0"
    port: int = 8501
    refresh_interval: int = 5  # seconds
    max_chart_points: int = 1000
    theme: str = "dark"
    
@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str = ""
    chat_id: str = ""
    enable_trade_alerts: bool = True
    enable_risk_alerts: bool = True
    enable_daily_summary: bool = True
    enable_goal_milestones: bool = True
    
@dataclass
class DatabaseConfig:
    """Database configuration"""
    db_path: str = "data/trading_bot.db"
    backup_interval: int = 3600  # seconds
    max_backup_files: int = 24
    
class ConfigManager:
    """Central configuration manager"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.env_file = self.config_dir / ".env"
        
        # Initialize configuration objects
        self.trading = TradingConfig()
        self.agents = AgentConfig()
        self.dashboard = DashboardConfig()
        self.telegram = TelegramConfig()
        self.database = DatabaseConfig()
        
        # Exchange configurations
        self.exchanges: Dict[str, ExchangeConfig] = {
            "binance": ExchangeConfig("binance"),
            "bybit": ExchangeConfig("bybit"),
            "okx": ExchangeConfig("okx"),
            "hyperliquid": ExchangeConfig("hyperliquid"),
            "gate": ExchangeConfig("gate"),
            "oanda": ExchangeConfig("oanda"),
            "icmarkets": ExchangeConfig("icmarkets"),
            "pepperstone": ExchangeConfig("pepperstone")
        }
        
        # Load configurations
        self.load_config()
        self.load_env()
        
    def load_config(self) -> None:
        """Load configuration from JSON file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    
                # Update trading config
                if 'trading' in config_data:
                    for key, value in config_data['trading'].items():
                        if hasattr(self.trading, key):
                            setattr(self.trading, key, value)
                            
                # Update agent config
                if 'agents' in config_data:
                    for key, value in config_data['agents'].items():
                        if hasattr(self.agents, key):
                            setattr(self.agents, key, value)
                            
                # Update dashboard config
                if 'dashboard' in config_data:
                    for key, value in config_data['dashboard'].items():
                        if hasattr(self.dashboard, key):
                            setattr(self.dashboard, key, value)
                            
                # Update telegram config
                if 'telegram' in config_data:
                    for key, value in config_data['telegram'].items():
                        if hasattr(self.telegram, key):
                            setattr(self.telegram, key, value)
                            
                # Update database config
                if 'database' in config_data:
                    for key, value in config_data['database'].items():
                        if hasattr(self.database, key):
                            setattr(self.database, key, value)
                            
                # Update exchange configs
                if 'exchanges' in config_data:
                    for exchange_name, exchange_data in config_data['exchanges'].items():
                        if exchange_name in self.exchanges:
                            for key, value in exchange_data.items():
                                if hasattr(self.exchanges[exchange_name], key):
                                    setattr(self.exchanges[exchange_name], key, value)
                                    
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            
    def save_config(self) -> None:
        """Save configuration to JSON file"""
        try:
            config_data = {
                'trading': asdict(self.trading),
                'agents': asdict(self.agents),
                'dashboard': asdict(self.dashboard),
                'telegram': asdict(self.telegram),
                'database': asdict(self.database),
                'exchanges': {name: asdict(config) for name, config in self.exchanges.items()}
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=4)
                
        except Exception as e:
            logging.error(f"Error saving config: {e}")
            
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
                exchange_config.passphrase = os.getenv(f"{exchange_name.upper()}_PASSPHRASE", "")
                
            # Load Telegram credentials
            self.telegram.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
            self.telegram.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
            
        except Exception as e:
            logging.error(f"Error loading environment variables: {e}")
            
    def validate_config(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate trading config
        if self.trading.max_leverage <= 0:
            errors.append("Max leverage must be positive")
        if self.trading.target_balance <= self.trading.starting_balance:
            errors.append("Target balance must be greater than starting balance")
        if not (0 < self.trading.max_risk_per_trade <= 0.1):
            errors.append("Max risk per trade must be between 0 and 10%")
        if not (0 < self.trading.max_daily_loss <= 0.2):
            errors.append("Max daily loss must be between 0 and 20%")
        if not (0 < self.trading.max_drawdown <= 0.5):
            errors.append("Max drawdown must be between 0 and 50%")
            
        # Validate agent config
        if not self.agents.llm_model:
            errors.append("LLM model must be specified")
        if not self.agents.ollama_base_url:
            errors.append("Ollama base URL must be specified")
            
        # Validate telegram config
        if self.telegram.enable_trade_alerts or self.telegram.enable_risk_alerts:
            if not self.telegram.bot_token:
                errors.append("Telegram bot token required when alerts are enabled")
            if not self.telegram.chat_id:
                errors.append("Telegram chat ID required when alerts are enabled")
                
        # Validate exchange configs
        active_exchanges = [name for name, config in self.exchanges.items() 
                          if config.api_key and config.api_secret]
        if not active_exchanges:
            errors.append("At least one exchange must be configured with API credentials")
            
        return errors
        
    def get_active_exchanges(self) -> List[str]:
        """Get list of exchanges with valid API credentials"""
        return [name for name, config in self.exchanges.items() 
                if config.api_key and config.api_secret]
                
    def update_goal(self, max_leverage: float, goal_command: str) -> None:
        """Update trading goal parameters"""
        self.trading.max_leverage = max_leverage
        self.trading.goal_command = goal_command
        
        # Parse target from goal command if possible
        try:
            if "to" in goal_command.lower():
                parts = goal_command.lower().split("to")
                if len(parts) > 1:
                    target_str = parts[1].split()[0].replace("$", "").replace(",", "")
                    self.trading.target_balance = float(target_str)
        except:
            pass
            
        self.save_config()

# Global configuration instance
config = ConfigManager()

if __name__ == "__main__":
    # Test configuration
    errors = config.validate_config()
    if errors:
        print("Configuration errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid!")
        print(f"Active exchanges: {config.get_active_exchanges()}")
