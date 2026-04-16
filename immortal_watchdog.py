#!/usr/bin/env python3
"""
UOTA Elite v2 - Immortal Watchdog Service
3-second auto-restart for 24/7 cloud operation
"""

# import os  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import subprocess  # Moved to function to avoid circular import
# import psutil  # Moved to function to avoid circular import
# import threading  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from pathlib import Path

class ImmortalWatchdog:
    """Immortal watchdog for 24/7 operation"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.agent_process = None
        self.agent_script = "master_controller.py"
        self.max_restart_attempts = 10000
        self.restart_delay = 3  # seconds
        self.is_running = True
        self.restart_count = 0
        
        # Windows-specific paths
        self.startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
        self.watchdog_script = os.path.abspath(__file__)
        
    def _setup_logging(self):
        """Setup logging for watchdog"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/immortal_watchdog.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def create_startup_entry(self):
        """Create Windows startup entry"""
        try:
            # import winshell  # Moved to function to avoid circular import
            from win32com.client import Dispatch
            
            startup_path = os.path.join(self.startup_folder, "UOTA_Immortal_Watchdog.lnk")
            
            # Create shortcut
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(startup_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.watchdog_script}"'
            shortcut.WorkingDirectory = os.path.dirname(self.watchdog_script)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            self.logger.info(f"✅ Startup entry created: {startup_path}")
            return True
            
        except ImportError:
            self.logger.warning("⚠️ winshell not available - manual setup required")
            self._manual_startup_instructions()
            return False
        except Exception as e:
            self.logger.error(f"❌ Error creating startup entry: {e}")
            return False
    
    def _manual_startup_instructions(self):
        """Provide manual startup instructions"""
        instructions = f"""
🔧 MANUAL STARTUP SETUP:
═══════════════════════════════════════
1. Open Task Scheduler (taskschd.msc)
2. Create Basic Task
3. Name: "UOTA Immortal Watchdog"
4. Trigger: At startup
5. Action: Start a program
6. Program: {sys.executable}
7. Arguments: "{self.watchdog_script}"
8. Start in: {os.path.dirname(self.watchdog_script)}
9. Finish with "Open Properties" checked
10. Check "Run with highest privileges"
11. Conditions tab: Uncheck "Start only if computer is on AC power"
12. Settings tab: Check "Allow task to be run on demand"
"""
        # # # # print(instructions)
        self.logger.info("Manual startup instructions provided")
    
    def is_process_running(self, process_name="master_controller.py"):
        """Check if agent process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and any(process_name in arg for arg in proc.info['cmdline']):
                    return proc
            return None
        except Exception as e:
            self.logger.error(f"❌ Error checking process: {e}")
            return None
    
    def start_agent(self):
        """Start the agent process"""
        try:
            self.logger.info("🚀 Starting UOTA Elite v2 agent...")
            
            # Start agent process
            self.agent_process = subprocess.Popen(
                [sys.executable, self.agent_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.restart_count += 1
            self.logger.info(f"✅ Agent started with PID: {self.agent_process.pid} (Restart #{self.restart_count})")
            
            # Send startup notification
            self._send_watchdog_notification("AGENT_STARTED", f"Agent restarted (#{self.restart_count})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error starting agent: {e}")
            return False
    
    def monitor_agent(self):
        """Monitor agent process and restart if needed"""
        try:
            while self.is_running and self.restart_count < self.max_restart_attempts:
                try:
                    # Check if agent is running
                    running_process = self.is_process_running()
                    
                    if running_process is None or (self.agent_process and self.agent_process.poll() is not None):
                        self.logger.warning("⚠️ Agent process not running - initiating restart...")
                        
                        # Log crash details
                        if self.agent_process:
                            stdout, stderr = self.agent_process.communicate()
                            if stderr:
                                self.logger.error(f"❌ Agent crash output: {stderr}")
                        
                        # Send crash notification
                        self._send_watchdog_notification("AGENT_CRASHED", f"Agent crashed, restarting in {self.restart_delay}s")
                        
                        # Restart agent
                        if self.start_agent():
                            self.logger.info(f"🔄 Agent restarted successfully")
                        else:
                            self.logger.error("❌ Failed to restart agent")
                            break
                    
                    # Wait before next check
                    time.sleep(0.1)
                    
                except KeyboardInterrupt:
                    self.logger.info("🛑 Watchdog stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f"❌ Error in monitoring: {e}")
                    time.sleep(0.1)
            
            self.logger.info(f"🔌 Watchdog stopped after {self.restart_count} restarts")
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in monitoring: {e}")
    
    def _send_watchdog_notification(self, event_type: str, message: str):
        """Send watchdog notification via Telegram"""
        try:
            from telegram_notifications import telegram_notifier
            
            notification = f"""
🔄 **IMMORTAL WATCHDOG**
═════════════════════════════════════
Event: {event_type}
Message: {message}
Time: {datetime.now().strftime('%H:%M:%S')}
Restarts: {self.restart_count}
Status: {'🟢 RUNNING' if self.is_running else '🔴 STOPPED'}
"""
            
            asyncio.create_task(telegram_notifier.send_message(notification))
            
        except Exception as e:
            # Don't let notification failure break watchdog
            self.logger.warning(f"⚠️ Failed to send watchdog notification: {e}")
    
    def get_watchdog_status(self) -> dict:
        """Get watchdog status"""
        return {
            'is_running': self.is_running,
            'restart_count': self.restart_count,
            'max_restarts': self.max_restart_attempts,
            'restart_delay': self.restart_delay,
            'agent_pid': self.agent_process.pid if self.agent_process else None,
            'uptime': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def run(self):
        """Main watchdog run method"""
        try:
            self.logger.info("🛡️ Immortal Watchdog starting...")
            self.logger.info(f"🎯 Target script: {self.agent_script}")
            self.logger.info(f"⏱️ Restart delay: {self.restart_delay} seconds")
            self.logger.info(f"🔄 Max restarts: {self.max_restart_attempts}")
            
            # Create startup entry
            self.create_startup_entry()
            
            # Start monitoring
            self.monitor_agent()
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in watchdog: {e}")
            sys.exit(1)

# Global watchdog instance
immortal_watchdog_instance = ImmortalWatchdog()

def main():
    """Main entry point"""
    immortal_watchdog_instance.run()

if __name__ == "__main__":
    main()
