#!/usr/bin/env python3
"""
UOTA Elite v2 - Cloud Watchdog for 24/7 Windows VPS
Perpetual self-healing with 10-second monitoring
"""

# import os
# import sys
# import time
# import logging
# import subprocess
# import psutil
# import threading
# import json
from datetime import datetime  # Moved to function to avoid circular import, timedelta
from pathlib import Path

class CloudWatchdog:
    """Cloud watchdog for 24/7 VPS operation"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.agent_process = None
        self.agent_script = "master_controller.py"
        self.monitor_interval = 10  # seconds
        self.max_restart_attempts = 10000
        self.restart_delay = 3  # seconds
        self.is_running = True
        self.restart_count = 0
        self.last_check_time = None
        
        # Windows-specific paths
        self.startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
        self.watchdog_script = os.path.abspath(__file__)
        self.log_file = "logs/cloud_watchdog.log"
        
        # Performance metrics
        self.uptime_start = datetime.now()
        self.total_downtime = timedelta()
        self.last_restart_time = None
        
    def _setup_logging(self):
        """Setup logging for cloud watchdog"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/cloud_watchdog.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def create_windows_startup(self):
        """Create Windows startup entry for auto-login"""
        try:
            # import winshell  # Moved to function to avoid circular import
            from win32com.client import Dispatch
            
            # Create watchdog startup shortcut
            watchdog_path = os.path.join(self.startup_folder, "UOTA_Cloud_Watchdog.lnk")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(watchdog_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.watchdog_script}"'
            shortcut.WorkingDirectory = os.path.dirname(self.watchdog_script)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            # Create agent startup shortcut
            agent_path = os.path.join(self.startup_folder, "UOTA_Agent.lnk")
            
            shortcut = shell.CreateShortCut(agent_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.agent_script}"'
            shortcut.WorkingDirectory = os.path.dirname(self.agent_script)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            self.logger.info(f" Windows startup entries created")
            self.logger.info(f"   Watchdog: {watchdog_path}")
            self.logger.info(f"   Agent: {agent_path}")
            
            return True
            
        except ImportError:
            self.logger.warning(" winshell not available - manual setup required")
            return self._manual_startup_instructions()
        except Exception as e:
            self.logger.error(f" Error creating Windows startup: {e}")
            return False
    
    def _manual_startup_instructions(self):
        """Provide manual startup instructions"""
        instructions = f"""
 MANUAL WINDOWS STARTUP SETUP:

1. Open Task Scheduler (taskschd.msc)
2. Create Basic Task
3. Name: "UOTA Cloud Watchdog"
4. Trigger: At startup
5. Action: Start a program
6. Program: {sys.executable}
7. Arguments: "{self.watchdog_script}"
8. Start in: {os.path.dirname(self.watchdog_script)}
9. Check: Run with highest privileges
10. Conditions tab: Uncheck "Start only if computer is on AC power"
11. Settings tab: Check "Allow task to be run on demand"
12. Finish with "Open Properties" checked
13. General tab: Select "Run whether user is logged on or not"
14. OK to save

Repeat for agent with:
Arguments: "{self.agent_script}"
"""
        print(instructions)
        self.logger.info("Manual startup instructions provided")
        return True
    
    def is_agent_running(self) -> bool:
        """Check if agent process is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and any(self.agent_script in arg for arg in proc.info['cmdline']):
                    return True
            return False
            
        except Exception as e:
            self.logger.error(f" Error checking agent process: {e}")
            return False
    
    def start_agent(self):
        """Start the agent process"""
        try:
            self.logger.info(f" Starting UOTA Elite v2 agent...")
            
            # Start agent process
            self.agent_process = subprocess.Popen(
                [sys.executable, self.agent_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            self.restart_count += 1
            self.last_restart_time = datetime.now()
            
            self.logger.info(f" Agent started with PID: {self.agent_process.pid} (Restart #{self.restart_count})")
            
            # Send startup notification
            self._send_watchdog_notification("AGENT_STARTED", f"Agent restarted (#{self.restart_count})")
            
            return True
            
        except Exception as e:
            self.logger.error(f" Error starting agent: {e}")
            return False
    
    def monitor_agent(self):
        """Monitor agent process with 10-second intervals"""
        try:
            while self.is_running and self.restart_count < self.max_restart_attempts:
                try:
                    current_time = datetime.now()
                    self.last_check_time = current_time
                    
                    # Check if agent is running
                    if not self.is_agent_running():
                        self.logger.warning(" Agent process not running - initiating restart...")
                        
                        # Log crash details
                        if self.agent_process:
                            stdout, stderr = self.agent_process.communicate()
                            if stderr:
                                self.logger.error(f" Agent crash output: {stderr}")
                        
                        # Send crash notification
                        self._send_watchdog_notification("AGENT_CRASHED", f"Agent crashed, restarting in {self.restart_delay}s")
                        
                        # Restart agent
                        if self.start_agent():
                            self.logger.info(f" Agent restarted successfully")
                        else:
                            self.logger.error(f" Failed to restart agent")
                            break
                    
                    # Update uptime metrics
                    self._update_performance_metrics()
                    
                    # Wait before next check
                    time.sleep(self.monitor_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info(" Watchdog stopped by user")
                    break
                except Exception as e:
                    self.logger.error(f" Error in monitoring loop: {e}")
                    time.sleep(self.monitor_interval)
            
            self.logger.info(f" Watchdog stopped after {self.restart_count} restarts")
            
        except Exception as e:
            self.logger.error(f" Fatal error in monitoring: {e}")
    
    def _update_performance_metrics(self):
        """Update performance metrics"""
        try:
            current_time = datetime.now()
            uptime = current_time - self.uptime_start
            
            # Calculate system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Log performance
            self.logger.debug(f" CPU: {cpu_percent:.1f}%, Memory: {memory.percent:.1f}%, Disk: {disk.percent:.1f}%")
            
            # Check for performance issues
            if cpu_percent > 90:
                self.logger.warning(f" High CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 85:
                self.logger.warning(f" High memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 90:
                self.logger.warning(f" High disk usage: {disk.percent:.1f}%")
                
        except Exception as e:
            self.logger.error(f" Error updating performance metrics: {e}")
    
    def _send_watchdog_notification(self, event_type: str, message: str):
        """Send watchdog notification via Telegram"""
        try:
            from telegram_notifications import telegram_notifier
            
            notification = f"""
 **CLOUD WATCHDOG**

Event: {event_type}
Message: {message}
Time: {datetime.now().strftime('%H:%M:%S')}
Restarts: {self.restart_count}
Uptime: {datetime.now() - self.uptime_start}
Status: {' RUNNING' if self.is_running else ' STOPPED'}
"""
            
            # Send notification asynchronously
            # import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(telegram_notifier.send_message(notification))
                else:
                    asyncio.run(telegram_notifier.send_message(notification))
            except:
                # Fallback to synchronous call
                pass
            
        except Exception as e:
            self.logger.warning(f" Failed to send watchdog notification: {e}")
    
    def get_watchdog_status(self) -> dict:
        """Get comprehensive watchdog status"""
        try:
            current_time = datetime.now()
            uptime = current_time - self.uptime_start
            
            return {
                'is_running': self.is_running,
                'restart_count': self.restart_count,
                'max_restarts': self.max_restart_attempts,
                'monitor_interval': self.monitor_interval,
                'restart_delay': self.restart_delay,
                'agent_pid': self.agent_process.pid if self.agent_process else None,
                'uptime_start': self.uptime_start.isoformat(),
                'current_time': current_time.isoformat(),
                'uptime_seconds': uptime.total_seconds(),
                'uptime_formatted': str(uptime),
                'last_restart_time': self.last_restart_time.isoformat() if self.last_restart_time else None,
                'last_check_time': self.last_check_time.isoformat() if self.last_check_time else None,
                'performance_metrics': {
                    'cpu_percent': psutil.cpu_percent(),
                    'memory_percent': psutil.virtual_memory().percent,
                    'disk_percent': psutil.disk_usage('/').percent
                }
            }
            
        except Exception as e:
            self.logger.error(f" Error getting watchdog status: {e}")
            return {}
    
    def run(self):
        """Main watchdog run method"""
        try:
            self.logger.info(" Cloud Watchdog starting...")
            self.logger.info(f" Target script: {self.agent_script}")
            self.logger.info(f" Monitor interval: {self.monitor_interval} seconds")
            self.logger.info(f" Max restarts: {self.max_restart_attempts}")
            
            # Create Windows startup entries
            self.create_windows_startup()
            
            # Start monitoring
            self.monitor_agent()
            
        except Exception as e:
            self.logger.error(f" Fatal error in cloud watchdog: {e}")
            sys.exit(1)
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            self.is_running = False
            
            if self.agent_process:
                self.agent_process.terminate()
                self.agent_process.wait(timeout=5)
            
            self.logger.info(" Cloud Watchdog cleanup complete")
            
        except Exception as e:
            self.logger.error(f" Error in cleanup: {e}")

def main():
    """Main entry point"""
    watchdog = CloudWatchdog()
    
    try:
        watchdog.run()
    except KeyboardInterrupt:
        print("\n Cloud Watchdog shutting down...")
        watchdog.cleanup()
    except Exception as e:
        print(f" Fatal error: {e}")
        watchdog.cleanup()

if __name__ == "__main__":
    main()
