"""
Crypto trade bot - Telegram Alerts System
Full Telegram integration with dedicated bot for real-time notifications
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import aiohttp
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import matplotlib.pyplot as plt
import io
import base64

from config import config
try:
    from risk_manager import risk_manager
except ImportError:
    risk_manager = None
    
try:
    from agents.supervisor import SupervisorAgent
except ImportError:
    SupervisorAgent = None
    
try:
    from opportunity_scanner import opportunity_scanner
except ImportError:
    opportunity_scanner = None

@dataclass
class AlertMessage:
    """Alert message data"""
    alert_type: str
    title: str
    message: str
    priority: str  # 'low', 'medium', 'high', 'critical'
    timestamp: datetime
    data: Optional[Dict[str, Any]] = None

class TelegramAlerts:
    """Telegram alerts system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.bot = None
        self.application = None
        self.is_running = False
        
        # Alert settings
        self.enabled_alerts = {
            'trade_alerts': config.telegram.enable_trade_alerts,
            'risk_alerts': config.telegram.enable_risk_alerts,
            'daily_summary': config.telegram.enable_daily_summary,
            'goal_milestones': config.telegram.enable_goal_milestones
        }
        
        # Alert history
        self.alert_history: List[AlertMessage] = []
        self.last_daily_summary = datetime.now().date()
        
        # Rate limiting
        self.last_alert_time = {}
        self.min_alert_interval = 60  # seconds
        
        # Initialize bot
        self._initialize_bot()
        
    def _initialize_bot(self) -> None:
        """Initialize Telegram bot"""
        try:
            if not config.telegram.bot_token or not config.telegram.chat_id:
                self.logger.warning("Telegram credentials not configured")
                return
                
            self.bot = Bot(token=config.telegram.bot_token)
            
            # Create application for handlers
            self.application = Application.builder().token(config.telegram.bot_token).build()
            
            # Add command handlers
            self.application.add_handler(CommandHandler("start", self._cmd_start))
            self.application.add_handler(CommandHandler("status", self._cmd_status))
            self.application.add_handler(CommandHandler("balance", self._cmd_balance))
            self.application.add_handler(CommandHandler("positions", self._cmd_positions))
            self.application.add_handler(CommandHandler("risk", self._cmd_risk))
            self.application.add_handler(CommandHandler("opportunities", self._cmd_opportunities))
            self.application.add_handler(CommandHandler("pause", self._cmd_pause))
            self.application.add_handler(CommandHandler("resume", self._cmd_resume))
            self.application.add_handler(CommandHandler("emergency", self._cmd_emergency))
            self.application.add_handler(CommandHandler("help", self._cmd_help))
            
            self.logger.info("Telegram bot initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing Telegram bot: {e}")
            
    async def start(self) -> None:
        """Start the Telegram bot"""
        try:
            if not self.application:
                self.logger.error("Telegram application not initialized")
                return
                
            self.is_running = True
            
            # Send startup message
            await self.send_alert(
                "system",
                "🤖 Crypto trade bot Started",
                "Trading system is now online and monitoring markets.",
                "medium"
            )
            
            # Start the bot
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.logger.info("Telegram bot started")
            
        except Exception as e:
            self.logger.error(f"Error starting Telegram bot: {e}")
            
    async def stop(self) -> None:
        """Stop the Telegram bot"""
        try:
            self.is_running = False
            
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
                
            self.logger.info("Telegram bot stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping Telegram bot: {e}")
            
    async def send_alert(self,
                        alert_type: str,
                        title: str,
                        message: str,
                        priority: str = "medium",
                        data: Optional[Dict[str, Any]] = None) -> bool:
        """Send an alert to Telegram"""
        try:
            if not self.bot or not self.enabled_alerts.get(f"{alert_type}_alerts", True):
                return False
                
            # Rate limiting
            current_time = datetime.now()
            if alert_type in self.last_alert_time:
                time_since_last = (current_time - self.last_alert_time[alert_type]).total_seconds()
                if time_since_last < self.min_alert_interval:
                    return False
                    
            self.last_alert_time[alert_type] = current_time
            
            # Format message based on priority
            priority_emoji = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }.get(priority, '⚪')
            
            # Create formatted message
            formatted_message = f"{priority_emoji} *{title}*\n\n"
            formatted_message += f"{message}\n\n"
            formatted_message += f"⏰ {current_time.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Add additional data if provided
            if data:
                formatted_message += "\n\n📊 *Details:*"
                for key, value in data.items():
                    if isinstance(value, float):
                        formatted_message += f"\n• {key.replace('_', ' ').title()}: {value:.4f}"
                    else:
                        formatted_message += f"\n• {key.replace('_', ' ').title()}: {value}"
                        
            # Send message
            await self.bot.send_message(
                chat_id=config.telegram.chat_id,
                text=formatted_message,
                parse_mode='Markdown'
            )
            
            # Store in history
            alert = AlertMessage(
                alert_type=alert_type,
                title=title,
                message=message,
                priority=priority,
                timestamp=current_time,
                data=data
            )
            self.alert_history.append(alert)
            
            # Keep only last 100 alerts
            if len(self.alert_history) > 100:
                self.alert_history = self.alert_history[-100:]
                
            self.logger.info(f"Telegram alert sent: {title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Telegram alert: {e}")
            return False
            
    async def send_trade_alert(self, 
                              symbol: str, 
                              side: str, 
                              amount: float, 
                              price: float,
                              order_type: str = "market") -> None:
        """Send trade execution alert"""
        try:
            side_emoji = "🟢" if side.lower() == "buy" else "🔴"
            
            title = f"{side_emoji} Trade Executed"
            message = f"**{side.upper()}** {amount:.4f} {symbol}\n"
            message += f"Price: ${price:.4f}\n"
            message += f"Type: {order_type.upper()}\n"
            message += f"Value: ${amount * price:.2f}"
            
            await self.send_alert(
                "trade",
                title,
                message,
                "medium",
                {
                    'symbol': symbol,
                    'side': side,
                    'amount': amount,
                    'price': price,
                    'value': amount * price
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error sending trade alert: {e}")
            
    async def send_position_close_alert(self,
                                      symbol: str,
                                      side: str,
                                      pnl: float,
                                      duration: timedelta) -> None:
        """Send position close alert"""
        try:
            pnl_emoji = "🟢" if pnl > 0 else "🔴"
            pnl_sign = "+" if pnl > 0 else ""
            
            title = f"{pnl_emoji} Position Closed"
            message = f"**{symbol}** {side.upper()} position closed\n"
            message += f"P&L: {pnl_sign}${pnl:.2f}\n"
            message += f"Duration: {duration}"
            
            priority = "high" if abs(pnl) > 100 else "medium"
            
            await self.send_alert(
                "trade",
                title,
                message,
                priority,
                {
                    'symbol': symbol,
                    'side': side,
                    'pnl': pnl,
                    'duration': str(duration)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error sending position close alert: {e}")
            
    async def send_risk_alert(self, 
                             alert_type: str,
                             message: str,
                             current_value: float,
                             limit_value: float) -> None:
        """Send risk management alert"""
        try:
            title = f"⚠️ Risk Alert: {alert_type}"
            
            priority = "critical" if current_value >= limit_value * 0.95 else "high"
            
            await self.send_alert(
                "risk",
                title,
                message,
                priority,
                {
                    'current_value': current_value,
                    'limit_value': limit_value,
                    'percentage': (current_value / limit_value) * 100
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error sending risk alert: {e}")
            
    async def send_opportunity_alert(self, 
                                   opportunity: Dict[str, Any]) -> None:
        """Send high-profit opportunity alert"""
        try:
            title = f"🎯 High-Confidence Opportunity"
            message = f"**{opportunity['symbol']}** - {opportunity['opportunity_type']}\n"
            message += f"Confidence: {opportunity['confidence']:.1%}\n"
            message += f"Expected Return: {opportunity['expected_return']:.1%}\n"
            message += f"Risk Level: {opportunity['risk_level']}\n"
            message += f"Catalyst: {opportunity['catalyst']}"
            
            priority = "high" if opportunity['confidence'] > 0.8 else "medium"
            
            await self.send_alert(
                "opportunity",
                title,
                message,
                priority,
                opportunity
            )
            
        except Exception as e:
            self.logger.error(f"Error sending opportunity alert: {e}")
            
    async def send_goal_milestone_alert(self, 
                                      progress_percentage: float,
                                      current_balance: float,
                                      target_balance: float) -> None:
        """Send goal milestone alert"""
        try:
            title = f"🎊 Goal Milestone Reached!"
            message = f"Progress: {progress_percentage:.1f}%\n"
            message += f"Current Balance: ${current_balance:.2f}\n"
            message += f"Target: ${target_balance:.2f}\n"
            message += f"Remaining: ${(target_balance - current_balance):.2f}"
            
            await self.send_alert(
                "goal",
                title,
                message,
                "medium",
                {
                    'progress_percentage': progress_percentage,
                    'current_balance': current_balance,
                    'target_balance': target_balance
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error sending goal milestone alert: {e}")
            
    async def send_daily_summary(self) -> None:
        """Send daily trading summary"""
        try:
            today = datetime.now().date()
            
            # Check if summary already sent today
            if today <= self.last_daily_summary:
                return
                
            self.last_daily_summary = today
            
            # Get daily metrics
            daily_pnl = risk_manager.metrics.daily_pnl
            daily_trades = len(risk_manager.daily_trades)
            win_rate = 0
            
            if daily_trades > 0:
                winning_trades = len([t for t in risk_manager.daily_trades if t['pnl'] > 0])
                win_rate = (winning_trades / daily_trades) * 100
                
            current_balance = risk_manager.metrics.current_balance
            goal_progress = ((current_balance - config.trading.starting_balance) / 
                           (config.trading.target_balance - config.trading.starting_balance)) * 100
            
            # Create summary message
            title = f"📊 Daily Summary - {today.strftime('%Y-%m-%d')}"
            message = f"**Daily P&L:** {'+' if daily_pnl > 0 else ''}${daily_pnl:.2f}\n"
            message += f"**Total Trades:** {daily_trades}\n"
            message += f"**Win Rate:** {win_rate:.1f}%\n"
            message += f"**Current Balance:** ${current_balance:.2f}\n"
            message += f"**Goal Progress:** {goal_progress:.1f}%\n"
            
            # Add best and worst trades
            if daily_trades > 0:
                best_trade = max(risk_manager.daily_trades, key=lambda x: x['pnl'])
                worst_trade = min(risk_manager.daily_trades, key=lambda x: x['pnl'])
                
                message += f"\n**Best Trade:** {best_trade['symbol']} +${best_trade['pnl']:.2f}\n"
                message += f"**Worst Trade:** {worst_trade['symbol']} ${worst_trade['pnl']:.2f}"
                
            await self.send_alert(
                "daily_summary",
                title,
                message,
                "low",
                {
                    'daily_pnl': daily_pnl,
                    'daily_trades': daily_trades,
                    'win_rate': win_rate,
                    'current_balance': current_balance,
                    'goal_progress': goal_progress
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error sending daily summary: {e}")
            
    async def send_system_alert(self, 
                               event_type: str,
                               message: str,
                               priority: str = "medium") -> None:
        """Send system event alert"""
        try:
            title = f"🔧 System Alert: {event_type}"
            
            await self.send_alert(
                "system",
                title,
                message,
                priority,
                {'event_type': event_type}
            )
            
        except Exception as e:
            self.logger.error(f"Error sending system alert: {e}")
            
    # Command handlers
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = """
🤖 *Crypto trade bot Trading Bot*

Welcome to your automated trading assistant!

*Available Commands:*
/status - System status
/balance - Account balance
/positions - Active positions
/risk - Risk metrics
/opportunities - Current opportunities
/pause - Pause trading
/resume - Resume trading
/emergency - Emergency stop
/help - Show this help

Stay tuned for real-time trading alerts! 🚀
        """
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /status command"""
        try:
            if not risk_manager:
                await update.message.reply_text("Risk manager not available")
                return
                
            status = risk_manager.get_risk_summary()
            
            message = f"📊 *System Status*\n\n"
            message += f"🔸 Trading Status: {status['trading_status']}\n"
            message += f"🔸 Current Balance: ${status['current_balance']:.2f}\n"
            message += f"🔸 Daily P&L: {'+' if status['daily_pnl'] > 0 else ''}${status['daily_pnl']:.2f}\n"
            message += f"🔸 Open Positions: {status['open_positions']}\n"
            message += f"🔸 Risk Score: {status['risk_score']:.1f}/100\n"
            message += f"🔸 Leverage Used: {status['leverage_used']:.1f}x"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error getting status: {e}")
            
    async def _cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /balance command"""
        try:
            if not risk_manager:
                await update.message.reply_text("Risk manager not available")
                return
                
            balance = risk_manager.metrics.current_balance
            daily_pnl = risk_manager.metrics.daily_pnl
            total_pnl = risk_manager.metrics.total_pnl
            
            message = f"💰 *Account Balance*\n\n"
            message += f"🔸 Current Balance: ${balance:.2f}\n"
            message += f"🔸 Daily P&L: {'+' if daily_pnl > 0 else ''}${daily_pnl:.2f}\n"
            message += f"🔸 Total P&L: {'+' if total_pnl > 0 else ''}${total_pnl:.2f}\n"
            
            # Add goal progress
            progress = ((balance - config.trading.starting_balance) / 
                       (config.trading.target_balance - config.trading.starting_balance)) * 100
            message += f"🔸 Goal Progress: {progress:.1f}%"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error getting balance: {e}")
            
    async def _cmd_positions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /positions command"""
        try:
            if not risk_manager:
                await update.message.reply_text("Risk manager not available")
                return
                
            positions = risk_manager.positions
            
            if not positions:
                await update.message.reply_text("No open positions")
                return
                
            message = f"📋 *Active Positions ({len(positions)})*\n\n"
            
            for symbol, pos in positions.items():
                pnl_emoji = "🟢" if pos.unrealized_pnl > 0 else "🔴"
                message += f"{pnl_emoji} *{symbol}*\n"
                message += f"  Side: {pos.side.upper()}\n"
                message += f"  Size: {pos.size:.4f}\n"
                message += f"  Entry: ${pos.entry_price:.4f}\n"
                message += f"  Current: ${pos.current_price:.4f}\n"
                message += f"  P&L: {'+' if pos.unrealized_pnl > 0 else ''}${pos.unrealized_pnl:.2f}\n"
                message += f"  Leverage: {pos.leverage:.1f}x\n\n"
                
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error getting positions: {e}")
            
    async def _cmd_risk(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /risk command"""
        try:
            risk_summary = risk_manager.get_risk_summary()
            
            message = f"⚠️ *Risk Management*\n\n"
            message += f"🔸 Risk Score: {risk_summary['risk_score']:.1f}/100\n"
            message += f"🔸 Daily Loss: {risk_summary['daily_loss_pct']:.1%}\n"
            message += f"🔸 Current Drawdown: {risk_summary['current_drawdown']:.1%}\n"
            message += f"🔸 Max Drawdown: {risk_summary['max_drawdown']:.1%}\n"
            message += f"🔸 Total Risk: ${risk_summary['total_risk']:.2f}\n"
            message += f"🔸 Leverage Used: {risk_summary['leverage_used']:.1f}x"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error getting risk info: {e}")
            
    async def _cmd_opportunities(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /opportunities command"""
        try:
            if not opportunity_scanner:
                await update.message.reply_text("Opportunity scanner not available")
                return
                
            opportunities = opportunity_scanner.get_latest_opportunities()
            
            if not opportunities:
                await update.message.reply_text("No current opportunities")
                return
                
            message = f"🎯 *Trading Opportunities ({len(opportunities)})*\n\n"
            
            for i, opp in enumerate(opportunities[:5]):  # Top 5
                confidence_emoji = "🟢" if opp.confidence > 0.8 else "🟡" if opp.confidence > 0.6 else "🔴"
                message += f"{confidence_emoji} *{opp.symbol}*\n"
                message += f"  Type: {opp.opportunity_type}\n"
                message += f"  Confidence: {opp.confidence:.1%}\n"
                message += f"  Expected Return: {opp.expected_return:.1%}\n"
                message += f"  Risk: {opp.risk_level}\n"
                message += f"  Catalyst: {opp.catalyst}\n\n"
                
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.message.reply_text(f"Error getting opportunities: {e}")
            
    async def _cmd_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /pause command"""
        try:
            if not risk_manager:
                await update.message.reply_text("Risk manager not available")
                return
                
            risk_manager.pause_trading("Manual pause via Telegram")
            await update.message.reply_text("⏸️ Trading paused")
            await self.send_system_alert("Manual Pause", "Trading paused via Telegram command", "medium")
            
        except Exception as e:
            await update.message.reply_text(f"Error pausing trading: {e}")
            
    async def _cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /resume command"""
        try:
            if not risk_manager:
                await update.message.reply_text("Risk manager not available")
                return
                
            risk_manager.resume_trading()
            await update.message.reply_text("▶️ Trading resumed")
            await self.send_system_alert("Manual Resume", "Trading resumed via Telegram command", "medium")
            
        except Exception as e:
            await update.message.reply_text(f"Error resuming trading: {e}")
            
    async def _cmd_emergency(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /emergency command"""
        try:
            if not risk_manager:
                await update.message.reply_text("Risk manager not available")
                return
                
            risk_manager.emergency_stop("Emergency stop via Telegram")
            await update.message.reply_text("🛑 EMERGENCY STOP ACTIVATED")
            await self.send_system_alert("Emergency Stop", "Emergency stop activated via Telegram", "critical")
            
        except Exception as e:
            await update.message.reply_text(f"Error in emergency stop: {e}")
            
    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command"""
        help_message = """
🤖 *UOTA Elite v2 - Help*

*Commands:*
/start - Welcome message
/status - System status and metrics
/balance - Account balance and P&L
/positions - Active positions
/risk - Risk management metrics
/opportunities - Current trading opportunities
/pause - Pause trading
/resume - Resume trading
/emergency - Emergency stop all trading
/help - Show this help message

*Alert Types:*
🟢 Low priority
🟡 Medium priority
🟠 High priority
🔴 Critical priority

Stay safe and trade smart! 🚀
        """
        
        await update.message.reply_text(help_message, parse_mode='Markdown')
        
    def get_alert_history(self, limit: int = 50) -> List[AlertMessage]:
        """Get recent alert history"""
        return self.alert_history[-limit:]
        
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert statistics"""
        if not self.alert_history:
            return {}
            
        total_alerts = len(self.alert_history)
        by_type = {}
        by_priority = {}
        
        for alert in self.alert_history:
            by_type[alert.alert_type] = by_type.get(alert.alert_type, 0) + 1
            by_priority[alert.priority] = by_priority.get(alert.priority, 0) + 1
            
        return {
            'total_alerts': total_alerts,
            'by_type': by_type,
            'by_priority': by_priority,
            'last_24h': len([a for a in self.alert_history 
                            if (datetime.now() - a.timestamp).total_seconds() < 86400])
        }

# Global Telegram alerts instance
telegram_alerts = TelegramAlerts()

if __name__ == "__main__":
    # Test Telegram alerts
    async def test_telegram():
        alerts = TelegramAlerts()
        
        # Send test alert
        await alerts.send_alert(
            "test",
            "Test Alert",
            "This is a test alert from UOTA Elite v2",
            "medium",
            {'test_data': 'example'}
        )
        
        print("Test alert sent")
        
    asyncio.run(test_telegram())
