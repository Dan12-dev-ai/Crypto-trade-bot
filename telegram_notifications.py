"""
UOTA Elite v2 - Telegram Bot Integration
24/7 communication for cloud deployment
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class TelegramConfig:
    """Telegram bot configuration"""
    bot_token: str
    chat_id: str
    enabled: bool = True
    notifications: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.notifications is None:
            self.notifications = {
                'smc_setups': True,
                'trade_entries': True,
                'trade_exits': True,
                'daily_limits': True,
                'errors': True,
                'system_status': True
            }

class TelegramNotifier:
    """Telegram bot notifier for 24/7 communication"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.bot = None
        self.last_notification_time = {}
        self.rate_limit_delay = 1.0  # seconds between notifications
        
        # Initialize bot if enabled
        if self.config.enabled:
            self._initialize_bot()
    
    def _load_config(self) -> TelegramConfig:
        """Load Telegram configuration from environment"""
        try:
            # Try to load from .env file
            env_file = ".env"
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('TELEGRAM_BOT_TOKEN='):
                            bot_token = line.split('=', 1)[1].strip()
                        elif line.startswith('TELEGRAM_CHAT_ID='):
                            chat_id = line.split('=', 1)[1].strip()
            
            return TelegramConfig(
                bot_token=bot_token if 'bot_token' in locals() else "",
                chat_id=chat_id if 'chat_id' in locals() else "",
                enabled=bool(bot_token and chat_id)
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error loading Telegram config: {e}")
            return TelegramConfig(bot_token="", chat_id="", enabled=False)
    
    def _initialize_bot(self):
        """Initialize Telegram bot"""
        try:
            from telegram import Bot
            
            self.bot = Bot(token=self.config.bot_token)
            
            # Check if there's an event loop running before creating task
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._test_connection())
            except RuntimeError:
                # No running event loop, we'll need to call _test_connection manually later if needed
                # or we just skip the test for now as the script using this will have its own loop
                pass
            
            self.logger.info("✅ Telegram bot initialized")
            
        except ImportError:
            self.logger.warning("⚠️ python-telegram-bot not installed")
            self.config.enabled = False
        except Exception as e:
            self.logger.error(f"❌ Error initializing Telegram bot: {e}")
            self.config.enabled = False
    
    async def _test_connection(self):
        """Test Telegram bot connection"""
        try:
            await self.bot.get_me()
            await self.send_message("🚀 UOTA Elite v2 - Telegram bot connected")
            self.logger.info("✅ Telegram bot connection tested")
        except Exception as e:
            self.logger.error(f"❌ Telegram bot connection failed: {e}")
            self.config.enabled = False
    
    async def send_message(self, message: str, notification_type: str = "general"):
        """Send message with rate limiting and error handling"""
        try:
            if not self.config.enabled or not self.bot:
                return False
            
            # Check if notification type is enabled
            if notification_type not in self.config.notifications:
                return False
            
            if not self.config.notifications.get(notification_type, True):
                return False
            
            # Rate limiting
            current_time = datetime.now()
            last_time = self.last_notification_time.get(notification_type, 0)
            
            if isinstance(last_time, str):
                last_time = datetime.fromisoformat(last_time)
            
            time_diff = (current_time - last_time).total_seconds()
            
            if time_diff < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - time_diff)
            
            # Send message
            await self.bot.send_message(
                chat_id=self.config.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Update last notification time
            self.last_notification_time[notification_type] = current_time.isoformat()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending Telegram message: {e}")
            return False
    
    async def notify_smc_setup(self, 
                              symbol: str,
                              setup_type: str,
                              confidence: float,
                              entry_price: float,
                              stop_loss: float,
                              take_profit: float):
        """Notify about new SMC setup"""
        if not self.config.notifications.get('smc_setups', True):
            return
        
        message = f"""
🔍 **NEW SMC SETUP IDENTIFIED**
═════════════════════════════════════
Symbol: {symbol}
Setup: {setup_type}
Confidence: {confidence:.1%}
Entry: ${entry_price:.5f}
Stop Loss: ${stop_loss:.5f}
Take Profit: ${take_profit:.5f}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: 🔍 ANALYZING
"""
        
        await self.send_message(message, "smc_setups")
    
    async def notify_trade_entry(self, 
                                symbol: str,
                                order_type: str,
                                volume: float,
                                entry_price: float,
                                order_id: int):
        """Notify about trade entry"""
        if not self.config.notifications.get('trade_entries', True):
            return
        
        message = f"""
🎯 **TRADE ENTERED**
═════════════════════════════════════
Symbol: {symbol}
Type: {order_type.upper()}
Volume: {volume} lots
Entry: ${entry_price:.5f}
Order ID: {order_id}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: 📈 ACTIVE
"""
        
        await self.send_message(message, "trade_entries")
    
    async def notify_trade_exit(self, 
                               symbol: str,
                               order_type: str,
                               volume: float,
                               entry_price: float,
                               exit_price: float,
                               profit_loss: float,
                               order_id: int):
        """Notify about trade exit"""
        if not self.config.notifications.get('trade_exits', True):
            return
        
        profit_emoji = "🟢" if profit_loss > 0 else "🔴"
        message = f"""
📊 **TRADE CLOSED**
═════════════════════════════════════
Symbol: {symbol}
Type: {order_type.upper()}
Volume: {volume} lots
Entry: ${entry_price:.5f}
Exit: ${exit_price:.5f}
P&L: {profit_emoji} ${profit_loss:.2f}
Order ID: {order_id}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: ✅ CLOSED
"""
        
        await self.send_message(message, "trade_exits")
    
    async def notify_daily_limit(self, 
                                limit_type: str,
                                current_value: float,
                                limit_value: float,
                                currency: str = "$"):
        """Notify about daily profit/loss limit"""
        if not self.config.notifications.get('daily_limits', True):
            return
        
        limit_emoji = "🟢" if limit_type == "PROFIT" else "🔴"
        message = f"""
📊 **DAILY {limit_type} LIMIT REACHED**
═════════════════════════════════════
Type: {limit_type}
Current: {currency}{current_value:.2f}
Limit: {currency}{limit_value:.2f}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: {limit_emoji} LIMIT REACHED
Action: 🛑 Trading paused for today
"""
        
        await self.send_message(message, "daily_limits")
    
    async def notify_system_status(self, 
                                  status: str,
                                  message: str,
                                  emoji: str = "ℹ️"):
        """Notify about system status"""
        if not self.config.notifications.get('system_status', True):
            return
        
        notification = f"""
{emoji} **SYSTEM STATUS**
═════════════════════════════════════
Status: {status}
Message: {message}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
        
        await self.send_message(notification, "system_status")
    
    async def notify_error(self, 
                         error_type: str,
                         error_message: str,
                         context: str = ""):
        """Notify about errors"""
        if not self.config.notifications.get('errors', True):
            return
        
        message = f"""
❌ **ERROR OCCURRED**
═════════════════════════════════════
Type: {error_type}
Message: {error_message}
Context: {context}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: ❌ ERROR
"""
        
        await self.send_message(message, "errors")
    
    async def send_daily_summary(self, 
                                trades_today: int,
                                profit_today: float,
                                skill_score: float,
                                balance: float):
        """Send daily performance summary"""
        message = f"""
📊 **DAILY PERFORMANCE SUMMARY**
═════════════════════════════════════
Date: {datetime.now().strftime('%Y-%m-%d')}
Trades Today: {trades_today}
Daily P&L: ${profit_today:.2f}
Skill Score: {skill_score:.1f}%
Current Balance: ${balance:.2f}
Status: {'🟢 PROFITABLE' if profit_today > 0 else '🔴 LOSS'}
"""
        
        await self.send_message(message, "system_status")
    
    async def send_startup_notification(self):
        """Send startup notification"""
        message = f"""
🚀 **UOTA ELITE v2 STARTED**
═════════════════════════════════════
Mode: CLOUD DEPLOYMENT
Platform: WINDOWS VPS
Status: 🟢 RUNNING
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Version: 2.0 - IMMORTAL AGENT
"""
        
        await self.send_message(message, "system_status")
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get Telegram configuration status"""
        return {
            'enabled': self.config.enabled,
            'bot_token_configured': bool(self.config.bot_token),
            'chat_id_configured': bool(self.config.chat_id),
            'notifications': self.config.notifications,
            'rate_limit': self.rate_limit_delay
        }

# Global telegram notifier instance
telegram_notifier = TelegramNotifier()
