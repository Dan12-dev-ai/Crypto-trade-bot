#!/usr/bin/env python3
"""
UOTA Elite v2 - Windows Watchdog Service
Immortal agent with 5-second auto-restart
"""

# import os  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import subprocess  # Moved to function to avoid circular import
# import psutil  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from pathlib import Path

class WindowsWatchdog:
    """Windows Watchdog for immortal agent deployment"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.agent_process = None
        self.agent_script = "master_controller.py"
        self.max_restart_attempts = 1000
        self.restart_delay = 5  # seconds
        self.is_running = True
        
        # Windows-specific paths
        self.startup_folder = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
        self.watchdog_script = os.path.abspath(__file__)
        
    def _setup_logging(self):
        """Setup logging for watchdog"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/watchdog.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def create_startup_shortcut(self):
        """Create Windows startup shortcut for auto-launch"""
        try:
            # import winshell  # Moved to function to avoid circular import
            from win32com.client import Dispatch
            
            shortcut_path = os.path.join(self.startup_folder, "UOTA_Watchdog.lnk")
            
            # Create shortcut
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = sys.executable
            shortcut.Arguments = f'"{self.watchdog_script}"'
            shortcut.WorkingDirectory = os.path.dirname(self.watchdog_script)
            shortcut.IconLocation = sys.executable
            shortcut.save()
            
            self.logger.info(f"✅ Startup shortcut created: {shortcut_path}")
            return True
            
        except ImportError:
            self.logger.warning("⚠️ winshell not available - manual startup setup required")
            self._manual_startup_instructions()
            return False
        except Exception as e:
            self.logger.error(f"❌ Error creating startup shortcut: {e}")
            return False
    
    def _manual_startup_instructions(self):
        """Provide manual startup instructions"""
        instructions = f"""
🔧 MANUAL STARTUP SETUP REQUIRED:
═══════════════════════════════════════
1. Open Task Scheduler (taskschd.msc)
2. Create Basic Task
3. Name: "UOTA Watchdog"
4. Trigger: At startup
5. Action: Start a program
6. Program: {sys.executable}
7. Arguments: "{self.watchdog_script}"
8. Start in: {os.path.dirname(self.watchdog_script)}
9. Finish with "Open Properties" checked
10. Check "Run with highest privileges"
11. Conditions tab: Uncheck "Start only if computer is on AC power"
"""
        print(instructions)
        self.logger.info("Manual startup instructions provided")
    
    def set_process_priority(self, process, priority="REAL_TIME"):
        """Set Windows process priority to Real-Time"""
        try:
            # import win32api  # Moved to function to avoid circular import, win32process, win32con
            
            # Get process handle
            handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, process.pid)
            
            # Set priority
            priority_map = {
                "IDLE": win32process.IDLE_PRIORITY_CLASS,
                "BELOW_NORMAL": win32process.BELOW_NORMAL_PRIORITY_CLASS,
                "NORMAL": win32process.NORMAL_PRIORITY_CLASS,
                "ABOVE_NORMAL": win32process.ABOVE_NORMAL_PRIORITY_CLASS,
                "HIGH": win32process.HIGH_PRIORITY_CLASS,
                "REAL_TIME": win32process.REALTIME_PRIORITY_CLASS
            }
            
            win32process.SetPriorityClass(handle, priority_map.get(priority, win32process.NORMAL_PRIORITY_CLASS))
            win32api.CloseHandle(handle)
            
            self.logger.info(f"✅ Process priority set to {priority}")
            return True
            
        except ImportError:
            self.logger.warning("⚠️ win32api not available - priority not set")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error setting process priority: {e}")
            return False
    
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
            
            # Set process priority to Real-Time
            self.set_process_priority(self.agent_process, "REAL_TIME")
            
            self.logger.info(f"✅ Agent started with PID: {self.agent_process.pid}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error starting agent: {e}")
            return False
    
    def monitor_agent(self):
        """Monitor agent process and restart if needed"""
        restart_count = 0
        
        while self.is_running and restart_count < self.max_restart_attempts:
            try:
                # Check if agent is running
                if self.agent_process is None or self.agent_process.poll() is not None:
                    self.logger.warning("⚠️ Agent process not running - initiating restart...")
                    
                    # Log crash details
                    if self.agent_process:
                        stdout, stderr = self.agent_process.communicate()
                        if stderr:
                            self.logger.error(f"❌ Agent crash output: {stderr}")
                    
                    # Restart agent
                    if self.start_agent():
                        restart_count += 1
                        self.logger.info(f"🔄 Agent restarted (attempt {restart_count})")
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
        
        self.logger.info(f"🔌 Watchdog stopped after {restart_count} restarts")
    
    def install_service(self):
        """Install as Windows service"""
        try:
            # # import win32service  # Moved to function to avoid circular importutil  # Moved to function to avoid circular import
            # import win32service  # Moved to function to avoid circular import
            # import win32event  # Moved to function to avoid circular import
            # import servicemanager  # Moved to function to avoid circular import
            
            class UOTAWatchdogService(win32serviceutil.ServiceFramework):
                _svc_name_ = "UOTAWatchdog"
                _svc_display_name_ = "UOTA Elite v2 Watchdog"
                _svc_description_ = "Immortal trading agent watchdog service"
                
                def __init__(self, args):
                    win32serviceutil.ServiceFramework.__init__(self, args)
                    self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
                    self.is_alive = True
                
                def SvcStop(self):
                    self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                    win32event.SetEvent(self.hWaitStop)
                    self.is_alive = False
                    servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                      servicemanager.PYS_SERVICE_STOPPED, self._svc_name_)
                
                def SvcDoRun(self):
                    servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                      servicemanager.PYS_SERVICE_STARTED, self._svc_name_)
                    self.main()
                
                def main(self):
                    watchdog = WindowsWatchdog()
                    watchdog.monitor_agent()
            
            # Install service
            win32serviceutil.InstallService(
                UOTAWatchdogService._svc_name_,
                UOTAWatchdogService._svc_display_name_,
                UOTAWatchdogService._svc_description_
            )
            
            self.logger.info("✅ Windows service installed successfully")
            return True
            
        except ImportError:
            self.logger.warning("⚠️ pywin32 not available - service installation skipped")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error installing service: {e}")
            return False
    
    def run(self):
        """Main watchdog run method"""
        try:
            self.logger.info("🛡️ UOTA Watchdog starting...")
            self.logger.info(f"🎯 Target script: {self.agent_script}")
            self.logger.info(f"⏱️ Restart delay: {self.restart_delay} seconds")
            self.logger.info(f"🔄 Max restarts: {self.max_restart_attempts}")
            
            # Create startup shortcut
            self.create_startup_shortcut()
            
            # Start monitoring
            self.monitor_agent()
            
        except Exception as e:
            self.logger.error(f"❌ Fatal error in watchdog: {e}")
            sys.exit(1)

def main():
    """Main entry point"""
    watchdog = WindowsWatchdog()
    watchdog.run()

if __name__ == "__main__":
    main()
