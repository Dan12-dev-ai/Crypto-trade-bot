#!/usr/bin/env python3
"""
UOTA Elite v2 - Autonomous Rollover System
30-day auto-renewal with logic lock
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class MissionLogic:
    """Mission logic configuration"""
    risk_rule_percent: float = 1.0  # Hard-locked 1%
    smc_confidence_threshold: float = 0.7  # Hard-locked 70%
    max_daily_trades: int = 10  # Hard-locked limit
    skill_score_threshold: float = 95.0  # Hard-locked 95%
    auto_renewal_enabled: bool = True  # Hard-locked enabled
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict):
        """Create from dictionary"""
        return cls(**data)

class AutonomousRollover:
    """Autonomous rollover system with logic lock"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mission_logic = MissionLogic()
        self.rollover_config_file = "data/rollover_config.json"
        self.last_rollover_date = None
        self.rollover_history = []
        
        # Load configuration
        self._load_rollover_config()
        
        # Hard-lock logic
        self._lock_mission_logic()
    
    def _load_rollover_config(self):
        """Load rollover configuration"""
        try:
            if Path(self.rollover_config_file).exists():
                with open(self.rollover_config_file, 'r') as f:
                    data = json.load(f)
                
                # Load mission logic
                if 'mission_logic' in data:
                    self.mission_logic = MissionLogic.from_dict(data['mission_logic'])
                
                # Load rollover history
                if 'rollover_history' in data:
                    self.rollover_history = data['rollover_history']
                
                # Load last rollover date
                if 'last_rollover_date' in data:
                    self.last_rollover_date = datetime.fromisoformat(data['last_rollover_date'])
                
                self.logger.info("✅ Rollover configuration loaded")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading rollover config: {e}")
    
    def _save_rollover_config(self):
        """Save rollover configuration"""
        try:
            Path("data").mkdir(exist_ok=True)
            
            config = {
                'mission_logic': self.mission_logic.to_dict(),
                'rollover_history': self.rollover_history,
                'last_rollover_date': self.last_rollover_date.isoformat() if self.last_rollover_date else None,
                'logic_locked': True,
                'auto_renewal_enabled': self.mission_logic.auto_renewal_enabled
            }
            
            with open(self.rollover_config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.logger.info("✅ Rollover configuration saved")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving rollover config: {e}")
    
    def _lock_mission_logic(self):
        """Hard-lock mission logic - cannot be changed"""
        try:
            # These values are hard-locked and cannot be changed
            locked_values = {
                'risk_rule_percent': 1.0,  # 1% absolute rule
                'smc_confidence_threshold': 0.7,  # 70% minimum confidence
                'skill_score_threshold': 95.0,  # 95% minimum skill score
                'auto_renewal_enabled': True  # Auto-renewal always enabled
            }
            
            # Apply locked values
            for key, value in locked_values.items():
                if hasattr(self.mission_logic, key):
                    setattr(self.mission_logic, key, value)
            
            self.logger.info("🔒 Mission logic hard-locked")
            
        except Exception as e:
            self.logger.error(f"❌ Error locking mission logic: {e}")
    
    def validate_trade_execution(self, trade_data: Dict) -> bool:
        """Validate trade against hard-locked logic"""
        try:
            # Check 1% risk rule
            risk_percent = trade_data.get('risk_percent', 0)
            if risk_percent > self.mission_logic.risk_rule_percent:
                self.logger.warning(f"❌ Trade rejected: Risk {risk_percent:.2f}% exceeds {self.mission_logic.risk_rule_percent:.1f}% limit")
                return False
            
            # Check SMC confidence
            smc_confidence = trade_data.get('smc_confidence', 0)
            if smc_confidence < self.mission_logic.smc_confidence_threshold:
                self.logger.warning(f"❌ Trade rejected: SMC confidence {smc_confidence:.2f} below {self.mission_logic.smc_confidence_threshold:.1f} threshold")
                return False
            
            # Check skill score
            from smc_logic_gate import SMCLogicGate
            smc_gate = SMCLogicGate()
            
            if smc_gate.skill_score < self.mission_logic.skill_score_threshold:
                self.logger.warning(f"❌ Trade rejected: Skill score {smc_gate.skill_score:.1f}% below {self.mission_logic.skill_score_threshold:.1f}% threshold")
                return False
            
            # Check daily trade limit
            today = datetime.now().date()
            today_trades = len([t for t in self.rollover_history if t.get('date') == today.isoformat()])
            
            if today_trades >= self.mission_logic.max_daily_trades:
                self.logger.warning(f"❌ Trade rejected: Daily trade limit {self.mission_logic.max_daily_trades} reached")
                return False
            
            # Log approved trade
            self._log_trade_execution(trade_data)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error validating trade execution: {e}")
            return False
    
    def _log_trade_execution(self, trade_data: Dict):
        """Log trade execution"""
        try:
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'date': datetime.now().date().isoformat(),
                'symbol': trade_data.get('symbol', ''),
                'type': trade_data.get('type', ''),
                'volume': trade_data.get('volume', 0),
                'risk_percent': trade_data.get('risk_percent', 0),
                'smc_confidence': trade_data.get('smc_confidence', 0),
                'skill_score': trade_data.get('skill_score', 0),
                'status': 'EXECUTED'
            }
            
            self.rollover_history.append(trade_log)
            
            # Keep only last 1000 trades
            if len(self.rollover_history) > 1000:
                self.rollover_history = self.rollover_history[-1000:]
            
            self._save_rollover_config()
            
        except Exception as e:
            self.logger.error(f"❌ Error logging trade execution: {e}")
    
    async def check_rollover_required(self, current_mission: Dict) -> bool:
        """Check if rollover is required"""
        try:
            if not self.mission_logic.auto_renewal_enabled:
                return False
            
            # Check if 30 days have passed since last rollover
            if self.last_rollover_date:
                days_since_rollover = (datetime.now() - self.last_rollover_date).days
                
                if days_since_rollover >= 30:
                    return True
            
            # Check if mission is expired
            if 'end_date' in current_mission:
                end_date = datetime.fromisoformat(current_mission['end_date'])
                
                if datetime.now() >= end_date:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Error checking rollover requirement: {e}")
            return False
    
    async def execute_rollover(self, old_mission: Dict) -> Dict:
        """Execute autonomous rollover"""
        try:
            self.logger.info("🔄 Executing autonomous rollover...")
            
            # Create new mission with same target
            new_target = old_mission.get('target_amount', 4000)
            new_start_date = datetime.now()
            new_end_date = new_start_date + timedelta(days=30)
            
            new_mission = {
                'target_amount': new_target,
                'start_date': new_start_date.isoformat(),
                'end_date': new_end_date.isoformat(),
                'status': 'AUTO-RENEWED',
                'mission_number': old_mission.get('mission_number', 1) + 1,
                'rollover_from': old_mission.get('mission_number', 1),
                'logic_locked': True
            }
            
            # Update last rollover date
            self.last_rollover_date = new_start_date
            
            # Log rollover
            rollover_log = {
                'timestamp': new_start_date.isoformat(),
                'type': 'AUTO_ROLLOVER',
                'old_mission': old_mission.get('mission_number', 1),
                'new_mission': new_mission['mission_number'],
                'target': new_target,
                'reason': '30-day auto-renewal'
            }
            
            self.rollover_history.append(rollover_log)
            
            # Save configuration
            self._save_rollover_config()
            
            # Send notification
            await self._send_rollover_notification(old_mission, new_mission)
            
            self.logger.info(f"✅ Rollover completed: Mission #{new_mission['mission_number']}")
            
            return new_mission
            
        except Exception as e:
            self.logger.error(f"❌ Error executing rollover: {e}")
            return old_mission
    
    async def _send_rollover_notification(self, old_mission: Dict, new_mission: Dict):
        """Send rollover notification"""
        try:
            from telegram_notifications import telegram_notifier
            
            message = f"""
🔄 **AUTONOMOUS ROLLOVER EXECUTED**
═════════════════════════════════════
Previous Mission: #{old_mission.get('mission_number', 1)}
New Mission: #{new_mission['mission_number']}
Target: ${new_mission['target_amount']:,.2f}
Start Date: {new_mission['start_date']}
End Date: {new_mission['end_date']}
Reason: 30-day auto-renewal
Logic: 🔒 HARD-LOCKED
Risk Rule: {self.mission_logic.risk_rule_percent:.1f}% (ABSOLUTE)
SMC Threshold: {self.mission_logic.smc_confidence_threshold:.1%} (MINIMUM)
Skill Threshold: {self.mission_logic.skill_score_threshold:.1f}% (MINIMUM)

Status: 🔄 AUTO-RENEWED
Time: {datetime.now().strftime('%H:%M:%S')}
"""
            
            await telegram_notifier.send_message(message)
            
        except Exception as e:
            self.logger.error(f"❌ Error sending rollover notification: {e}")
    
    def get_rollover_status(self) -> Dict:
        """Get rollover status"""
        try:
            days_since_rollover = 0
            if self.last_rollover_date:
                days_since_rollover = (datetime.now() - self.last_rollover_date).days
            
            return {
                'auto_renewal_enabled': self.mission_logic.auto_renewal_enabled,
                'last_rollover_date': self.last_rollover_date.isoformat() if self.last_rollover_date else None,
                'days_since_rollover': days_since_rollover,
                'rollover_history_count': len(self.rollover_history),
                'mission_logic': self.mission_logic.to_dict(),
                'logic_locked': True,
                'next_rollover_in': max(0, 30 - days_since_rollover)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting rollover status: {e}")
            return {}
    
    def get_daily_performance(self) -> Dict:
        """Get daily performance metrics"""
        try:
            today = datetime.now().date()
            today_trades = [t for t in self.rollover_history if t.get('date') == today.isoformat() and t.get('status') == 'EXECUTED']
            
            if not today_trades:
                return {
                    'date': today.isoformat(),
                    'trades': 0,
                    'profit_loss': 0.0,
                    'win_rate': 0.0,
                    'avg_confidence': 0.0,
                    'logic_compliance': 100.0
                }
            
            # Calculate metrics
            total_trades = len(today_trades)
            winning_trades = len([t for t in today_trades if t.get('profit', 0) > 0])
            total_profit = sum(t.get('profit', 0) for t in today_trades)
            avg_confidence = sum(t.get('smc_confidence', 0) for t in today_trades) / total_trades
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # Check logic compliance
            compliant_trades = len([t for t in today_trades if 
                                t.get('risk_percent', 0) <= self.mission_logic.risk_rule_percent and
                                t.get('smc_confidence', 0) >= self.mission_logic.smc_confidence_threshold])
            
            logic_compliance = (compliant_trades / total_trades) * 100 if total_trades > 0 else 100
            
            return {
                'date': today.isoformat(),
                'trades': total_trades,
                'profit_loss': total_profit,
                'win_rate': win_rate,
                'avg_confidence': avg_confidence,
                'logic_compliance': logic_compliance,
                'risk_rule_compliance': 100.0 - (len([t for t in today_trades if t.get('risk_percent', 0) > self.mission_logic.risk_rule_percent]) / total_trades * 100) if total_trades > 0 else 100.0,
                'smc_compliance': 100.0 - (len([t for t in today_trades if t.get('smc_confidence', 0) < self.mission_logic.smc_confidence_threshold]) / total_trades * 100) if total_trades > 0 else 100.0
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting daily performance: {e}")
            return {}
    
    def force_logic_lock(self):
        """Force logic lock - cannot be bypassed"""
        try:
            self._lock_mission_logic()
            
            # Save locked configuration
            self._save_rollover_config()
            
            self.logger.info("🔒 Mission logic force-locked")
            
        except Exception as e:
            self.logger.error(f"❌ Error force-locking logic: {e}")

# Global rollover instance
autonomous_rollover = AutonomousRollover()
