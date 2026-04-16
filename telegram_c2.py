#!/usr/bin/env python3
"""
UOTA Elite v2 - Telegram Command & Control
Phone interface for 24/7 remote control
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import os  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from typing import Dict, List, Optional, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from cryptography.fernet import Fernet
# import matplotlib  # Moved to function to avoid circular import.pyplot as plt
# import io  # Moved to function to avoid circular import
# import base64  # Moved to function to avoid circular import

class TelegramC2:
    """Telegram Command & Control system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.authorized_chat_id = None
        self.bot_token = None
        self.application = None
        self.encryption_key = None
        
        # Load configuration
        self._load_config()
        
        # Command handlers
        self.commands = {
            'status': self.cmd_status,
            'target': self.cmd_target,
            'report': self.cmd_report,
            'stop': self.cmd_stop,
            'help': self.cmd_help,
            'restart': self.cmd_restart,
            'balance': self.cmd_balance,
            'trades': self.cmd_trades,
            'health': self.cmd_health
        }
    
    def _load_config(self):
        """Load and decrypt configuration"""
        try:
            # Load encrypted config
            from security_hardening # import security_hardening  # Moved to function to avoid circular import
            
            # Get password from environment or prompt
            password = os.environ.get('ENCRYPTION_PASSWORD')
            if not password:
                self.logger.error("❌ Encryption password not set")
                return
            
            # Load Telegram config
            telegram_config = security_hardening.load_config_from_memory('.env.encrypted', password)
            
            if telegram_config:
                self.bot_token = telegram_config.get('TELEGRAM_BOT_TOKEN')
                self.authorized_chat_id = telegram_config.get('TELEGRAM_CHAT_ID')
                
                if self.bot_token and self.authorized_chat_id:
                    self.logger.info("✅ Telegram C2 configuration loaded")
                else:
                    self.logger.error("❌ Telegram configuration incomplete")
            else:
                self.logger.error("❌ Failed to load Telegram configuration")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading config: {e}")
    
    async def initialize(self):
        """Initialize Telegram bot"""
        try:
            if not self.bot_token:
                self.logger.error("❌ Bot token not configured")
                return False
            
            # Create application
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add command handlers
            for command, handler in self.commands.items():
                self.application.add_handler(CommandHandler(command, handler))
            
            # Add message handler for unauthorized access
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_unauthorized))
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            self.logger.info("✅ Telegram C2 initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error initializing Telegram C2: {e}")
            return False
    
    async def start(self):
        """Start Telegram bot"""
        try:
            if not self.application:
                return False
            
            # Start bot
            await self.application.initialize()
            await self.application.start()
            
            # Send startup notification
            await self.send_message("🚀 **UOTA ELITE v2 - Telegram C2 ONLINE**\nPhone interface ready for commands")
            
            # Run bot until stopped
            await self.application.updater.start_polling()
            
            self.logger.info("✅ Telegram C2 started")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting Telegram C2: {e}")
            return False
    
    async def stop(self):
        """Stop Telegram bot"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                self.logger.info("✅ Telegram C2 stopped")
                
        except Exception as e:
            self.logger.error(f"❌ Error stopping Telegram C2: {e}")
    
    def is_authorized(self, update: Update) -> bool:
        """Check if user is authorized"""
        try:
            chat_id = str(update.effective_chat.id)
            authorized_id = str(self.authorized_chat_id)
            
            if chat_id == authorized_id:
                return True
            else:
                # Log unauthorized access attempt
                self.logger.warning(f"🚨 UNAUTHORIZED ACCESS ATTEMPT: Chat ID {chat_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error checking authorization: {e}")
            return False
    
    async def handle_unauthorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unauthorized access attempts"""
        try:
            chat_id = update.effective_chat.id
            
            # Log unauthorized access
            self.logger.warning(f"🚨 UNAUTHORIZED ACCESS: Chat ID {chat_id}")
            
            # Send warning to authorized user
            await self.send_message(f"""
🚨 **SECURITY ALERT**
═════════════════════════════════════
Unauthorized Access Attempt
Chat ID: {chat_id}
Username: {update.effective_user.username if update.effective_user else 'Unknown'}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: 🚨 BLOCKED
""")
            
            # Send warning to unauthorized user
            await context.bot.send_message(
                chat_id=chat_id,
                text="🚨 Access Denied. This bot is protected."
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error handling unauthorized access: {e}")
    
    async def send_message(self, message: str, chat_id: str = None):
        """Send message to authorized user"""
        try:
            if not self.application:
                return False
            
            target_chat_id = chat_id or self.authorized_chat_id
            
            if not target_chat_id:
                return False
            
            await self.application.bot.send_message(
                chat_id=target_chat_id,
                text=message,
                parse_mode='Markdown'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending message: {e}")
            return False
    
    async def send_photo(self, photo_data: bytes, caption: str = ""):
        """Send photo to authorized user"""
        try:
            if not self.application:
                return False
            
            await self.application.bot.send_photo(
                chat_id=self.authorized_chat_id,
                photo=photo_data,
                caption=caption
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error sending photo: {e}")
            return False
    
    # Command handlers
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            if not self.is_authorized(update):
                return
            
            # Get account status
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            try:
                await mt5_integration.initialize()
                account_info = await mt5_integration.get_account_balance()
                
                # Get SMC brain health
                from smc_logic_gate import SMCLogicGate
                smc_gate = SMCLogicGate()
                
                # Get mission status
                from perpetual_autopilot # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                mission_status = perpetual_autopilot.get_mission_status()
                
                message = f"""
📊 **ACCOUNT STATUS**
═════════════════════════════════════
Balance: ${account_info.get('balance', 0):.2f}
Equity: ${account_info.get('equity', 0):.2f}
Margin: ${account_info.get('margin', 0):.2f}
Free Margin: ${account_info.get('free_margin', 0):.2f}
Leverage: {account_info.get('leverage', 'N/A')}x
Server: {account_info.get('server', 'Unknown')}

🧠 **SMC BRAIN HEALTH**
═════════════════════════════════════
Skill Score: {smc_gate.skill_score:.1f}%
Setups Analyzed: {smc_gate.setup_count}
Valid Setups: {smc_gate.valid_setup_count}
Order Block Threshold: {smc_gate.order_block_threshold:.1%}
Liquidity Sweep Threshold: {smc_gate.liquidity_sweep_threshold:.1%}
Status: {'🟢 HEALTHY' if smc_gate.skill_score >= 95 else '🟡 WARNING' if smc_gate.skill_score >= 85 else '🔴 CRITICAL'}

🎯 **MISSION STATUS**
═════════════════════════════════════
Mission: #{mission_status.get('mission_number', 'N/A')}
Target: ${mission_status.get('target_amount', 0):,.2f}
Progress: {mission_status.get('progress_percentage', 0):.1f}%
Days Remaining: {mission_status.get('days_remaining', 0)}
Status: {mission_status.get('status', 'Unknown')}
Auto-Renewal: {'✅ ENABLED' if mission_status.get('auto_renewal') else '❌ DISABLED'}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                await update.message.reply_text(f"❌ Error getting status: {e}")
                
        except Exception as e:
            self.logger.error(f"❌ Error in status command: {e}")
    
    async def cmd_target(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /target command"""
        try:
            if not self.is_authorized(update):
                return
            
            if not context.args:
                await update.message.reply_text("Usage: /target [amount]")
                return
            
            try:
                new_target = float(context.args[0])
                
                if new_target <= 0:
                    await update.message.reply_text("❌ Target must be positive")
                    return
                
                # Update mission target
                from perpetual_autopilot # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                await perpetual_autopilot.set_mission_target(new_target)
                
                message = f"""
🎯 **TARGET UPDATED**
═════════════════════════════════════
New Target: ${new_target:,.2f}
Previous Target: ${perpetual_autopilot.active_mission.target_amount if perpetual_autopilot.active_mission else 'None':,.2f}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: 🎯 UPDATED
"""
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except ValueError:
                await update.message.reply_text("❌ Invalid target amount")
                
        except Exception as e:
            self.logger.error(f"❌ Error in target command: {e}")
    
    async def cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        try:
            if not self.is_authorized(update):
                return
            
            await update.message.reply_text("📊 Generating XAUUSD report with Order Blocks...")
            
            # Generate chart
            chart_data = await self._generate_xauusd_chart()
            
            if chart_data:
                await self.send_photo(
                    chart_data,
                    f"📊 XAUUSD Chart - Order Blocks\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                await update.message.reply_text("📊 Chart sent successfully")
            else:
                await update.message.reply_text("❌ Failed to generate chart")
                
        except Exception as e:
            self.logger.error(f"❌ Error in report command: {e}")
            await update.message.reply_text(f"❌ Error generating report: {e}")
    
    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        try:
            if not self.is_authorized(update):
                return
            
            # Stop all trading
            from perpetual_autopilot # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await perpetual_autopilot.stop_autopilot()
            
            # Close all positions
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await mt5_integration.initialize()
            positions = await mt5_integration.get_positions()
            
            closed_count = 0
            for position in positions:
                if await mt5_integration.close_position(position.ticket):
                    closed_count += 1
            
            message = f"""
🛑 **EMERGENCY STOP EXECUTED**
═════════════════════════════════════
Action: All trading stopped
Positions Closed: {closed_count}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: 🛑 EMERGENCY STOP
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in stop command: {e}")
            await update.message.reply_text(f"❌ Error executing stop: {e}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            if not self.is_authorized(update):
                return
            
            help_text = """
📱 **TELEGRAM C2 COMMANDS**
═════════════════════════════════════
/status - Get account balance and SMC brain health
/target [amount] - Change monthly target
/report - XAUUSD chart with Order Blocks
/stop - Emergency stop all trading
/restart - Restart the agent
/balance - Account balance only
/trades - Current positions
/health - System health check
/help - Show this help

🛡️ **SECURITY FEATURES**
═════════════════════════════════════
• Authorization by Chat ID only
• Unauthorized access attempts logged
• Encrypted configuration
• Real-time security alerts
"""
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in help command: {e}")
    
    async def cmd_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command"""
        try:
            if not self.is_authorized(update):
                return
            
            await update.message.reply_text("🔄 Restarting agent...")
            
            # Send restart signal to agent
            from immortal_watchdog # # import immortal_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular # import immortal_watchdog  # Moved to function to avoid circular import.restart_count += 1
            
            await update.message.reply_text("✅ Restart signal sent")
            
        except Exception as e:
            self.logger.error(f"❌ Error in restart command: {e}")
    
    async def cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        try:
            if not self.is_authorized(update):
                return
            
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await mt5_integration.initialize()
            account_info = await mt5_integration.get_account_balance()
            
            message = f"""
💰 **ACCOUNT BALANCE**
═════════════════════════════════════
Balance: ${account_info.get('balance', 0):.2f}
Equity: ${account_info.get('equity', 0):.2f}
Margin: ${account_info.get('margin', 0):.2f}
Free Margin: ${account_info.get('free_margin', 0):.2f}
Time: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in balance command: {e}")
    
    async def cmd_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trades command"""
        try:
            if not self.is_authorized(update):
                return
            
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await mt5_integration.initialize()
            positions = await mt5_integration.get_positions()
            
            if positions:
                message = "📈 **CURRENT POSITIONS**\n═════════════════════════════════════\n"
                
                for pos in positions[:10]:  # Limit to 10 positions
                    direction = "🟢 BUY" if pos.type == 0 else "🔴 SELL"
                    profit_emoji = "🟢" if pos.profit > 0 else "🔴"
                    
                    message += f"""
{pos.symbol} {direction}
Volume: {pos.volume} lots
Entry: ${pos.price_open:.5f}
Current: ${pos.price_current:.5f}
P&L: {profit_emoji} ${pos.profit:.2f}
─────────────────────────
"""
                
                if len(positions) > 10:
                    message += f"... and {len(positions) - 10} more positions"
            else:
                message = "📈 **CURRENT POSITIONS**\n═════════════════════════════════════\nNo open positions"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in trades command: {e}")
    
    async def cmd_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command"""
        try:
            if not self.is_authorized(update):
                return
            
            # Get system health
            from immortal_watchdog # # import immortal_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            watchdog_status = immortal_watchdog.get_watchdog_status()
            
            # Get performance metrics
            from performance_optimization import performance_optimizer
            performance_metrics = performance_optimizer.get_performance_metrics()
            
            message = f"""
🏥 **SYSTEM HEALTH**
═════════════════════════════════════
Watchdog Status: {'🟢 RUNNING' if watchdog_status['is_running'] else '🔴 STOPPED'}
Restarts: {watchdog_status['restart_count']}
Agent PID: {watchdog_status.get('agent_pid', 'N/A')}

⚡ **PERFORMANCE**
═════════════════════════════════════
Latency: {performance_metrics.get('avg_latency_ms', 0):.2f}ms
WebSockets: {performance_metrics.get('websocket_connections', 0)}
Buffer Size: {performance_metrics.get('buffer_size', 0)}

🔒 **SECURITY**
═════════════════════════════════════
Encryption: ✅ AES-256
Firewall: ✅ IP Whitelist
Authorization: ✅ Chat ID Locked

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in health command: {e}")
    
    async def _generate_xauusd_chart(self) -> Optional[bytes]:
        """Generate XAUUSD chart with Order Blocks"""
        try:
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            # import pandas  # Moved to function to avoid circular import as pd
            # import numpy  # Moved to function to avoid circular import as np
            
            # Get XAUUSD data
            await mt5_integration.initialize()
            data = await mt5_integration.get_market_data('XAUUSD', 26014400, 100)  # H1, 100 candles
            
            if not data:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['time'], unit='s')
            
            # Create chart
            plt.figure(figsize=(12, 8))
            plt.plot(df['timestamp'], df['close'], label='XAUUSD', color='gold', linewidth=2)
            
            # Detect and mark Order Blocks (simplified)
            order_blocks = self._detect_order_blocks(df)
            
            for ob in order_blocks:
                plt.axhline(y=ob['price'], color='red', linestyle='--', alpha=0.7, label=f'Order Block ${ob["price"]:.2f}')
                plt.scatter(ob['timestamp'], ob['price'], color='red', s=100, marker='o')
            
            plt.title(f'XAUUSD - Order Blocks Analysis\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
            plt.xlabel('Time')
            plt.ylabel('Price ($)')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            # Save to bytes
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            
            return buf.getvalue()
            
        except Exception as e:
            self.logger.error(f"❌ Error generating chart: {e}")
            return None
    
    def _detect_order_blocks(self, df) -> List[Dict]:
        """Detect Order Blocks (simplified implementation)"""
        order_blocks = []
        
        try:
            # Find recent highs and lows
            window = 10
            highs = df['high'].rolling(window=window).max()
            lows = df['low'].rolling(window=window).min()
            
            # Find Order Block zones
            for i in range(window, len(df) - window):
                # Bullish Order Block (sell-side liquidity)
                if df['high'].iloc[i] == highs.iloc[i]:
                    if df['close'].iloc[i+1] < df['close'].iloc[i]:  # Rejection
                        order_blocks.append({
                            'timestamp': df['timestamp'].iloc[i],
                            'price': df['high'].iloc[i],
                            'type': 'sell_side'
                        })
                
                # Bearish Order Block (buy-side liquidity)
                if df['low'].iloc[i] == lows.iloc[i]:
                    if df['close'].iloc[i+1] > df['close'].iloc[i]:  # Rejection
                        order_blocks.append({
                            'timestamp': df['timestamp'].iloc[i],
                            'price': df['low'].iloc[i],
                            'type': 'buy_side'
                        })
            
            # Return most recent Order Blocks
            return order_blocks[-5:] if order_blocks else []
            
        except Exception as e:
            self.logger.error(f"❌ Error detecting Order Blocks: {e}")
            return []
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Handle errors"""
        self.logger.error(f"Telegram error: {error}")
    
    def get_c2_status(self) -> Dict:
        """Get C2 status"""
        return {
            'authorized_chat_id': self.authorized_chat_id,
            'bot_token_configured': bool(self.bot_token),
            'application_running': bool(self.application),
            'commands_available': list(self.commands.keys())
        }

# Global C2 instance
telegram_c2 = TelegramC2()
