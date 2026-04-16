"""
UOTA Elite v2 - Self-Healing Bridge
Auto-load mission state and resume trading without human intervention
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, Optional
from pathlib import Path

class SelfHealingBridge:
    """Self-healing bridge for perpetual operation"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mission_state_file = "data/active_mission.json"
        self.bridge_state_file = "data/bridge_state.json"
        
        # Bridge state
        self.bridge_state = {
            'last_connection': None,
            'connection_attempts': 0,
            'auto_recovery_enabled': True,
            'max_retry_attempts': 5,
            'retry_delay': 30  # seconds
        }
        
        # Load existing state
        self._load_bridge_state()
    
    def _load_bridge_state(self):
        """Load bridge state"""
        try:
            if Path(self.bridge_state_file).exists():
                with open(self.bridge_state_file, 'r') as f:
                    self.bridge_state = json.load(f)
                
                self.logger.info("✅ Bridge state loaded")
        except Exception as e:
            self.logger.error(f"❌ Error loading bridge state: {e}")
    
    def _save_bridge_state(self):
        """Save bridge state"""
        try:
            Path("data").mkdir(exist_ok=True)
            
            with open(self.bridge_state_file, 'w') as f:
                self.bridge_state['last_connection'] = datetime.now().isoformat()
                json.dump(self.bridge_state, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving bridge state: {e}")
    
    async def auto_load_mission_state(self):
        """Auto-load last saved mission state"""
        try:
            print("🔄 [HEALING]: Auto-loading mission state...")
            
            if Path(self.mission_state_file).exists():
                with open(self.mission_state_file, 'r') as f:
                    mission_data = json.load(f)
                
                # Convert dates
                mission_data['start_date'] = datetime.fromisoformat(mission_data['start_date'])
                mission_data['end_date'] = datetime.fromisoformat(mission_data['end_date'])
                
                print(f"""
🔄 [HEALING]: MISSION STATE LOADED
═════════════════════════════════════
Mission #{mission_data['mission_number']}
Target: ${mission_data['target_amount']:,.2f}
Start: {mission_data['start_date'].strftime('%Y-%m-%d')}
End: {mission_data['end_date'].strftime('%Y-%m-%d')}
Status: {mission_data['status']}
Auto-Renewal: {'ENABLED' if mission_data['auto_renewal'] else 'DISABLED'}

🚀 [HEALING]: Resuming perpetual operation...
""")
                
                return mission_data
            else:
                print("🔄 [HEALING]: No saved mission state found")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Error auto-loading mission state: {e}")
            return None
    
    async def heal_mt5_connection(self) -> bool:
        """Heal MT5 connection with retry logic"""
        try:
            print("🔄 [HEALING]: Attempting MT5 connection recovery...")
            
            if not self.bridge_state['auto_recovery_enabled']:
                print("❌ [HEALING]: Auto-recovery disabled")
                return False
            
            max_attempts = self.bridge_state['max_retry_attempts']
            retry_delay = self.bridge_state['retry_delay']
            
            for attempt in range(1, max_attempts + 1):
                print(f"🔄 [HEALING]: Connection attempt {attempt}/{max_attempts}")
                
                try:
                    # Test MT5 connection
                    from pymt5linux import MetaTrader5 as mt5
                    mt5_instance = mt5()
                    
                    if mt5_instance.initialize():
                        account_info = mt5_instance.account_info()
                        
                        if account_info:
                            print(f"""
✅ [HEALING]: CONNECTION RESTORED
═════════════════════════════════════
Account: {account_info.login}
Server: {account_info.server}
Balance: ${account_info.balance:.2f}
Equity: ${account_info.equity:.2f}
Attempts: {attempt}
""")
                            
                            # Update bridge state
                            self.bridge_state['connection_attempts'] = 0
                            self.bridge_state['last_connection'] = datetime.now().isoformat()
                            self._save_bridge_state()
                            
                            return True
                        else:
                            print("⚠️ [HEALING]: Connected but no account info")
                    
                except Exception as e:
                    print(f"❌ [HEALING]: Attempt {attempt} failed: {e}")
                
                if attempt < max_attempts:
                    print(f"🔄 [HEALING]: Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
            
            print(f"❌ [HEALING]: Connection failed after {max_attempts} attempts")
            self.bridge_state['connection_attempts'] += 1
            self._save_bridge_state()
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error in healing connection: {e}")
            return False
    
    async def monitor_connection_health(self):
        """Monitor connection health and auto-heal"""
        try:
            while self.is_running:
                await asyncio.sleep(60)  # Check every minute
                
                # Test MT5 connection
                try:
                    from pymt5linux import MetaTrader5 as mt5
                    mt5_instance = mt5()
                    
                    if not mt5_instance.initialize():
                        print("🔄 [HEALING]: Connection lost - initiating recovery...")
                        await self.heal_mt5_connection()
                    else:
                        # Connection is healthy
                        pass
                        
                except Exception as e:
                    print(f"🔄 [HEALING]: Connection error detected: {e}")
                    await self.heal_mt5_connection()
                    
        except Exception as e:
            self.logger.error(f"❌ Error in connection monitoring: {e}")
    
    async def resume_perpetual_operation(self):
        """Resume perpetual operation after healing"""
        try:
            # Load mission state
            mission_data = await self.auto_load_mission_state()
            
            if mission_data:
                # Restore perpetual autopilot
                from perpetual_autopilot # # import perpetual_autopilot  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                
                # Restore mission to autopilot
                from perpetual_autopilot import ActiveMission
                perpetual_autopilot.active_mission = ActiveMission(**mission_data)
                
                print("🚀 [HEALING]: Perpetual operation resumed")
                print("🔄 [HEALING]: Auto-renewal and monitoring active")
                
                # Start heartbeat monitor
                await perpetual_autopilot.start_perpetual_mode()
            else:
                print("🔄 [HEALING]: No mission to resume - awaiting command")
                
        except Exception as e:
            self.logger.error(f"❌ Error resuming perpetual operation: {e}")
    
    def get_healing_status(self) -> Dict:
        """Get healing status"""
        return {
            'auto_recovery_enabled': self.bridge_state['auto_recovery_enabled'],
            'connection_attempts': self.bridge_state['connection_attempts'],
            'last_connection': self.bridge_state['last_connection'],
            'max_retry_attempts': self.bridge_state['max_retry_attempts'],
            'retry_delay': self.bridge_state['retry_delay']
        }
    
    def enable_auto_recovery(self, enabled: bool):
        """Enable/disable auto recovery"""
        self.bridge_state['auto_recovery_enabled'] = enabled
        self._save_bridge_state()
        
        status = "ENABLED" if enabled else "DISABLED"
        print(f"🔄 [HEALING]: Auto-recovery {status}")

# Global self-healing bridge instance
self_healing_bridge = SelfHealingBridge()
