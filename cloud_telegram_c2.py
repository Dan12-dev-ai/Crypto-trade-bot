#!/usr/bin/env python3
"""
UOTA Elite v2 - Cloud Telegram C2
Remote control for 24/7 VPS operation
"""

# import asyncio
# import logging
# import json
# import os
# import matplotlib  # Moved to function to avoid circular import.pyplot as plt
# import io  # Moved to function to avoid circular import
# import base64  # Moved to function to avoid circular import
from datetime import datetime  # Moved to function to avoid circular import
from typing import Dict, List, Optional, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

class CloudTelegramC2:
    """Cloud Telegram Command & Control system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.authorized_chat_id = None
        self.bot_token = None
        self.application = None
        
        # Load configuration
        self._load_config()
        
        # Command handlers
        self.commands = {
            'status': self.cmd_status,
            'report': self.cmd_report,
            'kill': self.cmd_kill,
            'help': self.cmd_help,
            'restart': self.cmd_restart,
            'balance': self.cmd_balance,
            'trades': self.cmd_trades,
            'health': self.cmd_health,
            'uptime': self.cmd_uptime
        }
    
    def _load_config(self):
        """Load Telegram configuration"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.authorized_chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if self.bot_token and self.authorized_chat_id:
                self.logger.info(" Telegram C2 configuration loaded")
            else:
                self.logger.error(" Telegram C2 configuration incomplete")
                
        except Exception as e:
            self.logger.error(f" Error loading config: {e}")
    
    async def initialize(self):
        """Initialize Telegram bot"""
        try:
            if not self.bot_token:
                self.logger.error(" Bot token not configured")
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
            
            self.logger.info(" Cloud Telegram C2 initialized")
            return True
            
        except Exception as e:
            self.logger.error(f" Error initializing Telegram C2: {e}")
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
            await self.send_message(" **UOTA ELITE v2 - CLOUD C2 ONLINE**\n24/7 VPS Remote Control Ready")
            
            # Run bot until stopped
            await self.application.updater.start_polling()
            
            self.logger.info(" Cloud Telegram C2 started")
            
        except Exception as e:
            self.logger.error(f" Error starting Telegram C2: {e}")
            return False
    
    async def stop(self):
        """Stop Telegram bot"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                self.logger.info(" Cloud Telegram C2 stopped")
                
        except Exception as e:
            self.logger.error(f" Error stopping Telegram C2: {e}")
    
    def is_authorized(self, update: Update) -> bool:
        """Check if user is authorized"""
        try:
            chat_id = str(update.effective_chat.id)
            authorized_id = str(self.authorized_chat_id)
            
            if chat_id == authorized_id:
                return True
            else:
                # Log unauthorized access attempt
                self.logger.warning(f" UNAUTHORIZED ACCESS ATTEMPT: Chat ID {chat_id}")
                return False
                
        except Exception as e:
            self.logger.error(f" Error checking authorization: {e}")
            return False
    
    async def handle_unauthorized(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unauthorized access attempts"""
        try:
            chat_id = update.effective_chat.id
            
            # Log unauthorized access
            self.logger.warning(f" UNAUTHORIZED ACCESS: Chat ID {chat_id}")
            
            # Send warning to authorized user
            await self.send_message(f"""
 **SECURITY ALERT**

Unauthorized Access Attempt
Chat ID: {chat_id}
Username: {update.effective_user.username if update.effective_user else 'Unknown'}
Time: {datetime.now().strftime('%H:%M:%S')}
Status:  BLOCKED
""")
            
            # Send warning to unauthorized user
            await context.bot.send_message(
                chat_id=chat_id,
                text=" Access Denied. This is a protected trading bot."
            )
            
        except Exception as e:
            self.logger.error(f" Error handling unauthorized access: {e}")
    
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
            self.logger.error(f" Error sending message: {e}")
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
            self.logger.error(f" Error sending photo: {e}")
            return False
    
    # Command implementations
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
                
                # Get open trades
                positions = await mt5_integration.get_positions()
                
                # Get system health
                from cloud_watchdog # # # # # import cloud_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                watchdog_status = cloud_watchdog.get_watchdog_status()
                
                message = f"""
 **CLOUD STATUS REPORT**

 **ACCOUNT STATUS**
Balance: ${account_info.get('balance', 0):.2f}
Equity: ${account_info.get('equity', 0):.2f}
Margin: ${account_info.get('margin', 0):.2f}
Free Margin: ${account_info.get('free_margin', 0):.2f}
Leverage: {account_info.get('leverage', 'N/A')}x
Server: {account_info.get('server', 'Unknown')}

 **OPEN TRADES**
Total: {len(positions)}
{self._format_trades(positions[:5])}

 **SYSTEM HEALTH**
Watchdog: {' RUNNING' if watchdog_status.get('is_running') else ' STOPPED'}
Restarts: {watchdog_status.get('restart_count', 0)}
Uptime: {watchdog_status.get('uptime_formatted', 'Unknown')}
CPU: {watchdog_status.get('performance_metrics', {}).get('cpu_percent', 0):.1f}%
Memory: {watchdog_status.get('performance_metrics', {}).get('memory_percent', 0):.1f}%

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {' HUNTING' if len(positions) > 0 else ' WAITING'}
"""
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
            except Exception as e:
                await update.message.reply_text(f" Error getting status: {e}")
                
        except Exception as e:
            self.logger.error(f" Error in status command: {e}")
    
    async def cmd_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        try:
            if not self.is_authorized(update):
                return
            
            await update.message.reply_text(" Generating MT5 chart with SMC Order Blocks...")
            
            # Generate chart
            chart_data = await self._generate_mt5_chart()
            
            if chart_data:
                await self.send_photo(
                    chart_data,
                    f" MT5 Chart - SMC Order Blocks\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                await update.message.reply_text(" Chart sent successfully")
            else:
                await update.message.reply_text(" Failed to generate chart")
                
        except Exception as e:
            self.logger.error(f" Error in report command: {e}")
            await update.message.reply_text(f" Error generating report: {e}")
    
    async def cmd_kill(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /kill command"""
        try:
            if not self.is_authorized(update):
                return
            
            await update.message.reply_text(" KILLING ALL TRADES AND STOPPING BOT...")
            
            # Close all positions
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await mt5_integration.initialize()
            positions = await mt5_integration.get_positions()
            
            closed_count = 0
            for position in positions:
                if await mt5_integration.close_position(position.ticket):
                    closed_count += 1
            
            # Stop agent
            from cloud_watchdog # # # # # import cloud_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular # # # # import cloud_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import.is_running = False
            
            message = f"""
 **EMERGENCY KILL EXECUTED**

Action: All trades closed & bot stopped
Positions Closed: {closed_count}
Time: {datetime.now().strftime('%H:%M:%S')}
Status:  EMERGENCY STOP
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f" Error in kill command: {e}")
            await update.message.reply_text(f" Error executing kill: {e}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            if not self.is_authorized(update):
                return
            
            help_text = """
 **CLOUD C2 COMMANDS**

/status - Account balance, equity, open trades
/report - MT5 chart with SMC Order Blocks
/kill - Close all trades & stop bot
/restart - Restart the agent
/balance - Account balance only
/trades - Current open positions
/health - System health & uptime
/uptime - System uptime only
/help - Show this help

 **SECURITY FEATURES**

 Chat ID authorization only
 Unauthorized access alerts
 Encrypted communication
 Real-time notifications
"""
            
            await update.message.reply_text(help_text, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f" Error in help command: {e}")
    
    async def cmd_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command"""
        try:
            if not self.is_authorized(update):
                return
            
            await update.message.reply_text(" Restarting agent...")
            
            # Restart agent
            from cloud_watchdog # # # # # import cloud_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular # # # # import cloud_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import.restart_count += 1
            
            await update.message.reply_text(" Restart signal sent")
            
        except Exception as e:
            self.logger.error(f" Error in restart command: {e}")
            await update.message.reply_text(f" Error restarting: {e}")
    
    async def cmd_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /balance command"""
        try:
            if not self.is_authorized(update):
                return
            
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await mt5_integration.initialize()
            account_info = await mt5_integration.get_account_balance()
            
            message = f"""
 **ACCOUNT BALANCE**

Balance: ${account_info.get('balance', 0):.2f}
Equity: ${account_info.get('equity', 0):.2f}
Margin: ${account_info.get('margin', 0):.2f}
Free Margin: ${account_info.get('free_margin', 0):.2f}
Leverage: {account_info.get('leverage', 'N/A')}x
Server: {account_info.get('server', 'Unknown')}

Time: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f" Error in balance command: {e}")
            await update.message.reply_text(f" Error getting balance: {e}")
    
    async def cmd_trades(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /trades command"""
        try:
            if not self.is_authorized(update):
                return
            
            from mt5_integration # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await mt5_integration.initialize()
            positions = await mt5_integration.get_positions()
            
            if positions:
                message = f" **CURRENT TRADES**\n\n"
                message += self._format_trades(positions)
            else:
                message = " **CURRENT TRADES**\n\nNo open positions"
            
            message += f"\nTime: {datetime.now().strftime('%H:%M:%S')}"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f" Error in trades command: {e}")
            await update.message.reply_text(f" Error getting trades: {e}")
    
    async def cmd_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /health command"""
        try:
            if not self.is_authorized(update):
                return
            
            from cloud_watchdog # # # # # import cloud_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            watchdog_status = cloud_watchdog.get_watchdog_status()
            
            message = f"""
 **SYSTEM HEALTH**

Watchdog: {' RUNNING' if watchdog_status.get('is_running') else ' STOPPED'}
Restarts: {watchdog_status.get('restart_count', 0)}
Uptime: {watchdog_status.get('uptime_formatted', 'Unknown')}

 **PERFORMANCE METRICS**
CPU: {watchdog_status.get('performance_metrics', {}).get('cpu_percent', 0):.1f}%
Memory: {watchdog_status.get('performance_metrics', {}).get('memory_percent', 0):.1f}%
Disk: {watchdog_status.get('performance_metrics', {}).get('disk_percent', 0):.1f}%

 **NETWORK STATUS**
MT5 Connection: Testing...
Internet: Checking...

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {' HEALTHY' if watchdog_status.get('is_running') else ' ISSUES'}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f" Error in health command: {e}")
            await update.message.reply_text(f" Error getting health: {e}")
    
    async def cmd_uptime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /uptime command"""
        try:
            if not self.is_authorized(update):
                return
            
            from cloud_watchdog # # # # # import cloud_watchdog  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            watchdog_status = cloud_watchdog.get_watchdog_status()
            
            uptime_seconds = watchdog_status.get('uptime_seconds', 0)
            uptime_formatted = watchdog_status.get('uptime_formatted', 'Unknown')
            
            message = f"""
 **SYSTEM UPTIME**

Uptime: {uptime_formatted}
Seconds: {uptime_seconds}
Restarts: {watchdog_status.get('restart_count', 0)}
Last Restart: {watchdog_status.get('last_restart_time', 'Never')}

Time: {datetime.now().strftime('%H:%M:%S')}
Status: {' STABLE' if uptime_seconds > 3600 else ' RECENT'}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f" Error in uptime command: {e}")
            await update.message.reply_text(f" Error getting uptime: {e}")
    
    def _format_trades(self, positions: List) -> str:
        """Format trades for display"""
        try:
            if not positions:
                return "No open trades"
            
            formatted = ""
            for pos in positions:
                direction = " BUY" if pos.type == 0 else " SELL"
                profit_emoji = "" if pos.profit > 0 else ""
                
                formatted += f"""
{pos.symbol} {direction}
Volume: {pos.volume} lots
Entry: ${pos.price_open:.5f}
Current: ${pos.price_current:.5f}
P&L: {profit_emoji} ${pos.profit:.2f}

"""
            
            return formatted
            
        except Exception as e:
            self.logger.error(f" Error formatting trades: {e}")
            return "Error formatting trades"
    
    async def _generate_mt5_chart(self) -> Optional[bytes]:
        """Generate MT5 chart with SMC Order Blocks"""
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
            
            plt.title(f'XAUUSD - SMC Order Blocks\n{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
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
            self.logger.error(f" Error generating chart: {e}")
            return None
    
    def _detect_order_blocks(self, df) -> List[Dict]:
        """Detect Order Blocks (simplified implementation)"""
        try:
            order_blocks = []
            
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
            return order_blocks[-3:] if order_blocks else []
            
        except Exception as e:
            self.logger.error(f" Error detecting Order Blocks: {e}")
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

# Global Cloud C2 instance
cloud_telegram_c2 = CloudTelegramC2()

async def main():
    """Main entry point"""
    print(" Starting Cloud Telegram C2...")
    
    c2 = cloud_telegram_c2
    
    if await c2.initialize():
        await c2.start()
    else:
        print(" Failed to initialize Cloud Telegram C2")

if __name__ == "__main__":
    asyncio.run(main())
