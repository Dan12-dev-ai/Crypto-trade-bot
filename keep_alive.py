#!/usr/bin/env python3
"""
UOTA Elite v2 - Keep Alive Monitor
Lightweight watchdog using 0.1% CPU for 24/7 monitoring
"""

import os
import time
import json
import logging
import psutil
import subprocess
import signal
from datetime import datetime, timedelta
from typing import Dict, Optional

class KeepAliveMonitor:
    """Lightweight keep-alive monitor for zero-cost reliability"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.heartbeat_file = 'logs/heartbeat.log'
        self.bot_process = None
        self.monitoring_interval = 30.0  # 30 seconds
        self.heartbeat_timeout = 120.0  # 2 minutes
        self.max_restart_attempts = 10
        self.restart_count = 0
        self.is_running = False
        
        # Performance tracking
        self.last_cpu_check = 0
        self.cpu_check_interval = 60.0  # Check CPU every minute
        
    def _setup_logging(self):
        """Setup minimal logging (critical only)"""
        os.makedirs('logs', exist_ok=True)
        
        logging.basicConfig(
            level=logging.CRITICAL,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/keep_alive.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def check_heartbeat(self) -> bool:
        """Check if bot heartbeat is recent"""
        try:
            if not os.path.exists(self.heartbeat_file):
                self.logger.warning("⚠️ Heartbeat file not found")
                return False
            
            # Read heartbeat file
            with open(self.heartbeat_file, 'r') as f:
                heartbeat_data = json.load(f)
            
            last_heartbeat = datetime.fromisoformat(heartbeat_data['timestamp'])
            time_since_heartbeat = datetime.now() - last_heartbeat
            
            is_alive = time_since_heartbeat.total_seconds() < self.heartbeat_timeout
            
            if not is_alive:
                self.logger.critical(f"🚨 Heartbeat timeout: {time_since_heartbeat.total_seconds():.1f}s ago")
            
            return is_alive
            
        except Exception as e:
            self.logger.critical(f"❌ Error checking heartbeat: {e}")
            return False
    
    def get_bot_process(self) -> Optional[subprocess.Popen]:
        """Get the bot process"""
        try:
            # Find the main bot process by name or PID
            bot_name = 'python'  # Adjust based on your bot's process name
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python':
                        cmdline = proc.info['cmdline']
                        if cmdline and any('master_controller' in str(cmdline) or 'minimal_master' in str(cmdline)):
                            return proc
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return None
            
        except Exception as e:
            self.logger.critical(f"❌ Error getting bot process: {e}")
            return None
    
    def restart_bot(self) -> bool:
        """Restart the bot process"""
        try:
            self.logger.critical("🔄 Restarting bot process...")
            
            # Kill existing bot process
            if self.bot_process:
                try:
                    self.bot_process.terminate()
                    self.bot_process.wait(timeout=10)
                    self.logger.info("✅ Bot process terminated")
                except subprocess.TimeoutExpired:
                    self.bot_process.kill()
                    self.logger.warning("⚠️ Bot process killed")
                except Exception as e:
                    self.logger.error(f"❌ Error killing bot process: {e}")
            
            # Start new bot process
            try:
                # Start minimal master controller
                new_process = subprocess.Popen([
                    'python', 'minimal_master_controller.py'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=os.getcwd())
                
                self.bot_process = new_process
                self.restart_count += 1
                
                self.logger.critical(f"✅ Bot restarted: PID {new_process.pid} (Restart #{self.restart_count})")
                
                return True
                
            except Exception as e:
                self.logger.critical(f"❌ Error starting bot process: {e}")
                return False
                
        except Exception as e:
            self.logger.critical(f"❌ Error restarting bot: {e}")
            return False
    
    def check_cpu_usage(self) -> float:
        """Check CPU usage efficiently"""
        try:
            current_time = time.time()
            
            # Only check CPU every minute to save resources
            if current_time - self.last_cpu_check < self.cpu_check_interval:
                return 0.0
            
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.last_cpu_check = current_time
            
            return cpu_percent
            
        except Exception as e:
            self.logger.error(f"❌ Error checking CPU usage: {e}")
            return 0.0
    
    def send_telegram_heartbeat(self):
        """Send heartbeat to Telegram"""
        try:
            # Import here to avoid circular imports
            from cloud_telegram_c2 import cloud_telegram_c2
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': self.check_cpu_usage(),
                'restart_count': self.restart_count,
                'status': 'MONITORING_ACTIVE'
            }
            
            message = f"""
💓 **KEEP ALIVE HEARTBEAT**
═══════════════════════════════════
Timestamp: {metrics['timestamp']}
CPU Usage: {metrics['cpu_usage']:.1f}%
Restarts: {metrics['restart_count']}
Status: 🟢 MONITORING ACTIVE
Process: PID {self.bot_process.pid if self.bot_process else 'Unknown'}
"""
            
            # Send asynchronously
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(cloud_telegram_c2.send_message(message))
                else:
                    asyncio.run(cloud_telegram_c2.send_message(message))
            except Exception as e:
                self.logger.error(f"❌ Error sending Telegram heartbeat: {e}")
                
        except Exception as e:
            self.logger.error(f"❌ Error in Telegram heartbeat: {e}")
    
    def run_keep_alive_monitor(self):
        """Run the keep-alive monitor"""
        try:
            self.logger.info("🔄 Starting keep-alive monitor...")
            self.is_running = True
            
            while self.is_running:
                try:
                    # Sleep to use minimal CPU (0.1% target)
                    time.sleep(self.monitoring_interval)
                    
                    # Check heartbeat
                    if not self.check_heartbeat():
                        self.logger.critical("🚨 Bot heartbeat lost - Restarting...")
                        
                        if self.restart_bot():
                            self.logger.info("✅ Bot restarted successfully")
                        else:
                            self.logger.error("❌ Bot restart failed")
                            
                            if self.restart_count >= self.max_restart_attempts:
                                self.logger.critical("🚨 Max restart attempts reached - Stopping monitor")
                                break
                    
                    # Update bot process reference
                    self.bot_process = self.get_bot_process()
                    
                    # Send Telegram heartbeat every 5 minutes (10 cycles)
                    if int(time.time()) % 300 == 0:
                        self.send_telegram_heartbeat()
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 Keep-alive monitor stopped by user")
                    break
                except Exception as e:
                    self.logger.critical(f"❌ Error in keep-alive loop: {e}")
                    time.sleep(self.monitoring_interval)
            
            self.is_running = False
            
        except Exception as e:
            self.logger.critical(f"❌ Fatal error in keep-alive monitor: {e}")
    
    def stop(self):
        """Stop the keep-alive monitor"""
        self.is_running = False
        self.logger.info("🛑 Keep-alive monitor stopped")
        
        # Terminate bot process if running
        if self.bot_process:
            try:
                self.bot_process.terminate()
                self.logger.info("✅ Bot process terminated")
            except Exception as e:
                self.logger.error(f"❌ Error terminating bot: {e}")

# Global keep-alive monitor
keep_alive_monitor = KeepAliveMonitor()

def main():
    """Main entry point"""
    print("🔄 Starting Keep Alive Monitor...")
    
    monitor = keep_alive_monitor
    
    try:
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            print(f"\n🛑 Received signal {signum} - Shutting down...")
            monitor.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Run the monitor
        monitor.run_keep_alive_monitor()
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        print("🔄 Keep Alive Monitor stopped")

if __name__ == "__main__":
    main()
