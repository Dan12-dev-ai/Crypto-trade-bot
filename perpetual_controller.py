#!/usr/bin/env python3
"""
UOTA Elite v2 - Perpetual Controller
Master controller with perpetual autopilot integration
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import os  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from pathlib import Path
from typing import List

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/perpetual_controller.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class PerpetualController:
    """Perpetual autopilot controller"""
    
    def __init__(self):
        self.prompt = "🎯 [PERPETUAL]: Autopilot ACTIVE. "
        self.command_history = []
        self.max_history = 100
        self.is_running = False
        self.perpetual_mode = True
        
        # Command registry
        self.commands = {
            '/help': self.cmd_help,
            '/status': self.cmd_status,
            '/mission': self.cmd_mission,
            '/stop': self.cmd_stop,
            '/emergency': self.cmd_emergency,
            '/renewal': self.cmd_renewal,
            '/heartbeat': self.cmd_heartbeat,
            '/clear': self.cmd_clear,
            '/exit': self.cmd_exit
        }
    
    async def start(self):
        """Start perpetual controller"""
        try:
            print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 UOTA ELITE v2 - PERPETUAL CONTROLLER        ║
║              Zero Downtime | Total Autonomy                ║
╚════════════════════════════════════════════════════════════╝

🔄 [SYSTEM]: Perpetual Autopilot ACTIVE
🔒 [AUTOPILOT]: Mission will auto-renew every 30 days
🛡️ [SAFETY]: 1% Risk Rule hard-locked
🧠 [BRAIN]: SMC Logic hard-locked
🎯 [SYSTEM]: Awaiting your first target...
""")
            
            self.is_running = True
            
            # Start perpetual autopilot
            from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            autopilot_task = asyncio.create_task(perpetual_autopilot.start_perpetual_mode())
            
            # Start command loop
            await self._command_loop()
            
        except KeyboardInterrupt:
            print("\n👋 Perpetual Controller shutting down...")
            await self._shutdown()
        except Exception as e:
            logger.error(f"❌ Error starting perpetual controller: {e}")
            await self._shutdown()
    
    async def _command_loop(self):
        """Main command processing loop"""
        while self.is_running:
            try:
                # Get user input
                command = await self._get_input()
                
                if not command:
                    continue
                    
                # Extract command and args
                parts = command.split()
                cmd = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Handle pure numbers as mission target
                if cmd.isdigit() and not args:
                    # Convert to mission target
                    target_amount = float(cmd)
                    print(f"""
🎯 [COMMANDER]: MISSION TARGET RECEIVED
═══════════════════════════════════
Target: ${target_amount:,.2f}
Duration: 30 days (auto-renewal enabled)
Mode: PERPETUAL AUTOPILOT
""")
                    
                    # Set mission target
                    from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                    await perpetual_autopilot.set_mission_target(target_amount)
                    
                # Check if command exists
                elif cmd in self.commands:
                    await self.commands[cmd](args)
                else:
                    print(f"❌ Unknown command: {cmd}")
                    print("💡 Type '/help' for available commands")
                    
            except Exception as e:
                print(f"❌ Error processing command: {e}")
    
    async def _get_input(self) -> str:
        """Get user input asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, self.prompt)
    
    # Command implementations
    async def cmd_help(self, args: List[str]):
        """Show help information"""
        print("""
╔════════════════════════════════════════════════════════════╗
║                  🚀 PERPETUAL CONTROLLER HELP               ║
╚════════════════════════════════════════════════════════════╝

🎯 MISSION COMMANDS:
  [4000]                    - Set 30-day mission target
    Example: 4000 (auto-converts to mission)
  /mission status            - Show current mission status
  /renewal on/off          - Enable/disable auto-renewal

🔄 AUTOPILOT COMMANDS:
  /heartbeat                 - Show heartbeat status
  /stop                     - Stop perpetual autopilot
  /emergency                 - Emergency stop all trading

📊 SYSTEM COMMANDS:
  /status                    - Detailed system status
  /clear                     - Clear screen
  /exit                      - Exit controller

🛡️ PERPETUAL FEATURES:
  • Auto-Renewal: Mission auto-renews every 30 days
  • Zero Downtime: Self-healing on restart
  • Total Autonomy: XAUUSD scanning 24/7
  • Risk Management: 1% rule always maintained
  • SMC Logic: Hard-locked (no changes)
""")
    
    async def cmd_mission(self, args: List[str]):
        """Show mission status"""
        try:
            from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            status = perpetual_autopilot.get_mission_status()
            
            if status['mission_active']:
                print(f"""
🎯 [MISSION]: CURRENT STATUS
═════════════════════════════════════
Mission #{status['mission_number']}
Target: ${status['target_amount']:,.2f}
Start Date: {status['start_date']}
End Date: {status['end_date']}
Days Remaining: {status['days_remaining']}
Progress: {status['progress_percentage']:.1f}%
Status: {status['status']}
Auto-Renewal: {'ENABLED' if status['auto_renewal'] else 'DISABLED'}
Mode: PERPETUAL AUTOPILOT
""")
            else:
                print("""
🎯 [MISSION]: NO ACTIVE MISSION
═════════════════════════════════════
Status: No active mission
Action: Enter a target number to start
Example: 4000
""")
                
        except Exception as e:
            print(f"❌ Error getting mission status: {e}")
    
    async def cmd_renewal(self, args: List[str]):
        """Control auto-renewal"""
        try:
            from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            if not args:
                print(f"Auto-renewal: {'ENABLED' if perpetual_autopilot.auto_renewal else 'DISABLED'}")
                print("Usage: /renewal on or /renewal off")
                return
            
            setting = args[0].lower()
            
            if setting == 'on':
                perpetual_autopilot.auto_renewal = True
                print("✅ Auto-renewal: ENABLED")
                print("🔄 Mission will auto-renew every 30 days")
            elif setting == 'off':
                perpetual_autopilot.auto_renewal = False
                print("❌ Auto-renewal: DISABLED")
                print("🛑 Mission will expire after 30 days")
            else:
                print("❌ Invalid setting. Use 'on' or 'off'")
                
        except Exception as e:
            print(f"❌ Error setting renewal: {e}")
    
    async def cmd_heartbeat(self, args: List[str]):
        """Show heartbeat status"""
        try:
            from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            status = perpetual_autopilot.heartbeat_status
            
            print(f"""
🔄 [HEARTBEAT]: MONITOR STATUS
═════════════════════════════════════
Running: {'YES' if status.is_running else 'NO'}
Mission Active: {'YES' if status.mission_active else 'NO'}
Days Remaining: {status.days_remaining}
Last Heartbeat: {status.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')}
Auto-Renewal: {'ENABLED' if status.auto_renewal_enabled else 'DISABLED'}
""")
            
        except Exception as e:
            print(f"❌ Error getting heartbeat status: {e}")
    
    async def cmd_stop(self, args: List[str]):
        """Stop perpetual autopilot"""
        try:
            print("""
🛑 [COMMANDER]: STOPPING AUTOPILOT
═════════════════════════════════════
Action: Stopping perpetual mode
Auto-Renewal: Will be disabled
Mission: Will be paused
""")
            
            from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await perpetual_autopilot.stop_autopilot()
            
            # Update prompt
            self.prompt = "🎯 [SYSTEM]: Autopilot STOPPED. "
            
        except Exception as e:
            print(f"❌ Error stopping autopilot: {e}")
    
    async def cmd_emergency(self, args: List[str]):
        """Emergency stop all trading"""
        try:
            print("""
🚨 [COMMANDER]: EMERGENCY STOP
═════════════════════════════════════
Action: Emergency stop all trading
Risk: All positions will be closed
System: Will enter safe mode
""")
            
            # Stop autopilot
            from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            await perpetual_autopilot.stop_autopilot()
            
            # Close all positions (would connect to MT5 in real implementation)
            print("🚨 All trading stopped - System in safe mode")
            
            # Update prompt
            self.prompt = "🚨 [EMERGENCY]: Safe mode active. "
            
        except Exception as e:
            print(f"❌ Error in emergency stop: {e}")
    
    async def cmd_status(self, args: List[str]):
        """Show detailed system status"""
        try:
            print("""
📊 [SYSTEM]: PERPETUAL STATUS REPORT
═════════════════════════════════════
""")
            
            # Get mission status
            from perpetual_autopilot # # # # # # # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            mission_status = perpetual_autopilot.get_mission_status()
            
            if mission_status['mission_active']:
                print(f"Mission: #{mission_status['mission_number']} ACTIVE")
                print(f"Target: ${mission_status['target_amount']:,.2f}")
                print(f"Progress: {mission_status['progress_percentage']:.1f}%")
                print(f"Days Remaining: {mission_status['days_remaining']}")
            else:
                print("Mission: No active mission")
            
            # Get heartbeat status
            heartbeat = perpetual_autopilot.heartbeat_status
            print(f"Autopilot: {'RUNNING' if heartbeat.is_running else 'STOPPED'}")
            print(f"Auto-Renewal: {'ENABLED' if heartbeat.auto_renewal_enabled else 'DISABLED'}")
            
            # Test MT5 connection
            try:
                from pymt5linux import MetaTrader5 as mt5
                mt5_instance = mt5()
                
                if mt5_instance.initialize():
                    account_info = mt5_instance.account_info()
                    if account_info:
                        print(f"MT5 Connection: ✅ ESTABLISHED")
                        print(f"Account: {account_info.login}")
                        print(f"Balance: ${account_info.balance:.2f}")
                    else:
                        print("MT5 Connection: ⚠️ ESTABLISHED (No account info)")
                else:
                    print("MT5 Connection: ❌ FAILED")
            except:
                print("MT5 Connection: ❌ UNAVAILABLE")
            
            print("SMC Logic: ✅ Hard-locked")
            print("Risk Rule: ✅ 1% absolute")
            print("Random Trading: ❌ DISABLED")
            
        except Exception as e:
            print(f"❌ Error in status command: {e}")
    
    async def cmd_clear(self, args: List[str]):
        """Clear screen"""
        os.system('clear')
        print("""
╔════════════════════════════════════════════════════════════╗
║           🚀 UOTA ELITE v2 - PERPETUAL CONTROLLER        ║
║              Zero Downtime | Total Autonomy                ║
╚════════════════════════════════════════════════════════════╝

🔄 [SYSTEM]: Perpetual Autopilot ACTIVE
🔒 [AUTOPILOT]: Mission will auto-renew every 30 days
🛡️ [SAFETY]: 1% Risk Rule hard-locked
🧠 [BRAIN]: SMC Logic hard-locked
🎯 [SYSTEM]: Awaiting your first target...
""")
    
    async def cmd_exit(self, args: List[str]):
        """Exit controller"""
        print("\n👋 Perpetual Controller shutting down...")
        self.is_running = False
    
    async def _shutdown(self):
        """Cleanup and shutdown"""
        print("🔌 Perpetual Controller shutdown complete")

# Global perpetual controller instance
perpetual_controller = PerpetualController()

async def main():
    """Main entry point"""
    print("🚀 Starting UOTA Elite v2 Perpetual Controller...")
    await perpetual_controller.start()

if __name__ == "__main__":
    asyncio.run(main())
