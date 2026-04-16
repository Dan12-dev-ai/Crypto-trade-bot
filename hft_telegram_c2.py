#!/usr/bin/env python3
"""
UOTA Elite v2 - HFT Telegram Command & Control
Free monitoring with heartbeat command for 24/7 operation
"""

import asyncio
import logging
import json
import os
import psutil
from datetime import datetime
from typing import Dict, List, Optional, Any
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

class HFTTelegramC2:
    """HFT Telegram Command & Control system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.authorized_chat_id = None
        self.bot_token = None
        self.application = None
        
        # Command handlers
        self.commands = {
            'heartbeat': self.cmd_heartbeat,
            'status': self.cmd_status,
            'performance': self.cmd_performance,
            'restart': self.cmd_restart,
            'stop': self.cmd_stop,
            'help': self.cmd_help,
            'memory': self.cmd_memory,
            'cpu': self.cmd_cpu,
            'uptime': self.cmd_uptime
        }
        
    def _setup_logging(self):
        """Setup minimal logging"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.CRITICAL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/hft_telegram_c2.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _load_config(self):
        """Load Telegram configuration"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            self.authorized_chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if self.bot_token and self.authorized_chat_id:
                self.logger.info("✅ Telegram C2 configuration loaded")
            else:
                self.logger.error("❌ Telegram C2 configuration incomplete")
                
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
            
            # Add error handler
            self.application.add_error_handler(self.error_handler)
            
            self.logger.info("✅ HFT Telegram C2 initialized")
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
            await self.send_message("🚀 **HFT TELEGRAM C2 ONLINE**\n24/7 High-Frequency Trading Control Ready")
            
            self.logger.info("✅ HFT Telegram C2 started")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting Telegram C2: {e}")
            return False
    
    async def stop(self):
        """Stop Telegram bot"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
                self.logger.info("✅ HFT Telegram C2 stopped")
                
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
                # Log unauthorized access
                self.logger.critical(f"🚨 UNAUTHORIZED ACCESS: Chat ID {chat_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error checking authorization: {e}")
            return False
    
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
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE, error: Exception):
        """Handle errors"""
        self.logger.critical(f"❌ Telegram error: {error}")
    
    # Command implementations
    async def cmd_heartbeat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /heartbeat command"""
        try:
            if not self.is_authorized(update):
                return
            
            # Check if bot is alive
            bot_alive = await self._check_bot_alive()
            
            if bot_alive:
                status = "🟢 ALIVE"
                message = f"""
💓 **BOT HEARTBEAT**
═══════════════════════════════════
Status: {status}
Timestamp: {datetime.now().strftime('%H:%M:%S')}
CPU Usage: {psutil.cpu_percent():.1f}%
Memory: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB
Uptime: {self._get_uptime()}
Status: 🎯 HUNTING
"""
            else:
                status = "🔴 NOT RESPONDING"
                message = f"""
💓 **BOT HEARTBEAT**
═══════════════════════════════════
Status: {status}
Timestamp: {datetime.now().strftime('%H:%M:%S')}
⚠️ Bot not responding - Check keep_alive.py
Action: Manual restart may be needed
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in heartbeat command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            if not self.is_authorized(update):
                return
            
            # Get bot status
            bot_alive = await self._check_bot_alive()
            
            message = f"""
📊 **HFT BOT STATUS**
═══════════════════════════════════
Status: {'🟢 RUNNING' if bot_alive else '🔴 STOPPED'}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
CPU Usage: {psutil.cpu_percent():.1f}%
Memory Usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB
Uptime: {self._get_uptime()}
Process ID: {os.getpid()}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in status command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_performance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /performance command"""
        try:
            if not self.is_authorized(update):
                return
            
            # Get performance metrics
            process = psutil.Process()
            
            message = f"""
⚡ **PERFORMANCE METRICS**
═════════════════════════════════════
CPU Usage: {psutil.cpu_percent(interval=1):.1f}%
Memory Usage: {process.memory_info().rss / 1024 / 1024:.1f}MB
Memory Percent: {process.memory_percent():.1f}%
Disk Usage: {psutil.disk_usage('/').percent:.1f}%
Active Threads: {len(process.threads())}
Open Files: {len(process.open_files()) if hasattr(process, 'open_files') else 0}
Network Connections: {len(process.connections())}
Timestamp: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in performance command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_restart(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /restart command"""
        try:
            if not self.is_authorized(update):
                return
            
            await update.message.reply_text("🔄 Restarting bot...")
            
            # Restart bot
            from keep_alive import keep_alive_monitor
            success = keep_alive_monitor.restart_bot()
            
            if success:
                await update.message.reply_text("✅ Bot restart initiated")
            else:
                await update.message.reply_text("❌ Bot restart failed")
            
        except Exception as e:
            self.logger.error(f"❌ Error in restart command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        try:
            if not self.is_authorized(update):
                return
            
            await update.message.reply_text("🛑 Stopping bot...")
            
            # Stop bot
            from keep_alive import keep_alive_monitor
            keep_alive_monitor.stop()
            
            await update.message.reply_text("✅ Bot stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error in stop command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /memory command"""
        try:
            if not self.is_authorized(update):
                return
            
            process = psutil.Process()
            memory_info = process.memory_info()
            
            message = f"""
🧠 **MEMORY USAGE**
═════════════════════════════════════
RSS Memory: {memory_info.rss / 1024 / 1024:.1f}MB
VMS Memory: {memory_info.vms / 1024 / 1024:.1f}MB
Shared Memory: {memory_info.shared / 1024 / 1024:.1f}MB
Text Memory: {memory_info.text / 1024:.1f}MB
Lib Memory: {memory_info.lib / 1024 / 1024:.1f}MB
Dirty Memory: {memory_info.dirty / 1024 / 1024:.1f}MB
Percent: {process.memory_percent():.1f}%
Timestamp: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in memory command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_cpu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cpu command"""
        try:
            if not self.is_authorized(update):
                return
            
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            message = f"""
⚡ **CPU USAGE**
═════════════════════════════════════
CPU Usage: {cpu_percent:.1f}%
CPU Count: {cpu_count}
CPU Frequency: {cpu_freq.current:.1f}MHz if cpu_freq.current else 'Unknown'}
Load Average: {psutil.getloadavg()[0]:.2f} if hasattr(psutil, 'getloadavg') else 'N/A'}
Per CPU: {cpu_percent / cpu_count:.1f}%
Timestamp: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in CPU command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_uptime(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /uptime command"""
        try:
            if not self.is_authorized(update):
                return
            
            uptime_str = self._get_uptime()
            
            message = f"""
⏰ **SYSTEM UPTIME**
═════════════════════════════════════
Uptime: {uptime_str}
Boot Time: {datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S')}
Timestamp: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in uptime command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        try:
            if not self.is_authorized(update):
                return
            
            message = """
📱 **HFT TELEGRAM C2 COMMANDS**
═════════════════════════════════════
/heartbeat - Check if bot is alive
/status - Bot status and performance
/performance - Detailed performance metrics
/restart - Restart the bot
/stop - Stop the bot
/memory - Memory usage details
/cpu - CPU usage details
/uptime - System uptime
/help - Show this help

💡 Free Monitoring: All commands are 100% free
🚀 High-Frequency: Optimized for speed
🛡️ Security: Chat ID authorization only
"""
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"❌ Error in help command: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def _check_bot_alive(self) -> bool:
        """Check if bot is alive"""
        try:
            # Check if heartbeat file exists and is recent
            heartbeat_file = 'logs/heartbeat.log'
            
            if not os.path.exists(heartbeat_file):
                return False
            
            with open(heartbeat_file, 'r') as f:
                heartbeat_data = json.load(f)
            
            last_heartbeat = datetime.fromisoformat(heartbeat_data['timestamp'])
            time_since_heartbeat = datetime.now() - last_heartbeat
            
            return time_since_heartbeat.total_seconds() < 120  # 2 minutes
            
        except Exception as e:
            self.logger.error(f"❌ Error checking bot alive: {e}")
            return False
    
    def _get_uptime(self) -> str:
        """Get formatted uptime string"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            return f"{days}d {hours}h {minutes}m"
            
        except Exception as e:
            self.logger.error(f"❌ Error getting uptime: {e}")
            return "Unknown"

# Global HFT Telegram C2 instance
hft_telegram_c2 = HFTTelegramC2()

async def main():
    """Main entry point"""
    print("📱 Starting HFT Telegram C2...")
    
    c2 = hft_telegram_c2
    
    try:
        # Load configuration
        c2._load_config()
        
        # Initialize
        if await c2.initialize():
            # Start bot
            await c2.start()
        else:
            print("❌ Failed to initialize HFT Telegram C2")
            
    except Exception as e:
        print(f"❌ Fatal error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
