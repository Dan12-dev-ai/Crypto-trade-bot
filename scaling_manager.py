"""
UOTA Elite v2 - Professional Scaling Manager
Handles account scaling while maintaining 1% risk rule
"""

# import json  # Moved to function to avoid circular import
# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
# import os  # Moved to function to avoid circular import

@dataclass
class ScalingPhase:
    """Scaling phase configuration"""
    phase: str
    balance_range: List[float]
    max_position_size: float
    daily_trades_limit: int

class ScalingManager:
    """Professional account scaling manager"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config_file = "scaling_config.json"
        self.config = {}
        self.current_phase = None
        self.performance_log = []
        
        # Load configuration
        self._load_config()
        
    def _load_config(self):
        """Load scaling configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                self.logger.info("✅ Scaling configuration loaded")
            else:
                self.logger.error(f"❌ Configuration file not found: {self.config_file}")
                self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"❌ Error loading configuration: {e}")
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default configuration"""
        self.config = {
            "risk_management": {
                "max_risk_per_trade": 0.01,
                "max_daily_loss": 0.05,
                "max_drawdown": 0.20
            },
            "lot_size_calculation": {
                "method": "fixed_risk_percentage",
                "risk_percentage": 0.01,
                "minimum_lot_size": 0.01,
                "maximum_lot_size": 5.0
            },
            "performance_metrics": {
                "skill_score_threshold": 95.0,
                "win_rate_target": 70.0
            }
        }
    
    async def upscale_account(self, target_amount: float) -> bool:
        """Upscale account to target amount while maintaining risk rules"""
        try:
            # Get current balance
            from mt5_integration # import mt5_integration  # Moved to function to avoid circular import
            balance_info = await mt5_integration.get_account_balance()
            current_balance = balance_info.get('equity', 1000.0)
            
            self.logger.info(f"🎯 Upscaling account: ${current_balance:.2f} → ${target_amount:.2f}")
            
            # Validate target
            if target_amount <= current_balance:
                self.logger.warning(f"⚠️ Target amount (${target_amount:.2f}) must be greater than current balance (${current_balance:.2f})")
                return False
            
            # Check skill score
            from smc_logic_gate # import smc_logic_gate  # Moved to function to avoid circular import
            skill_score = smc_logic_gate.get_skill_score()
            
            if skill_score < self.config.get('performance_metrics', {}).get('skill_score_threshold', 95.0):
                self.logger.error(f"❌ Skill score too low: {skill_score:.1f}% < 95%")
                return False
            
            # Calculate new lot sizes
            new_lot_sizes = await self._calculate_scaled_lot_sizes(target_amount)
            
            # Update configuration
            await self._update_scaling_config(target_amount, new_lot_sizes)
            
            # Log the scaling event
            scaling_event = {
                'timestamp': datetime.now().isoformat(),
                'action': 'upscale',
                'previous_balance': current_balance,
                'target_balance': target_amount,
                'skill_score': skill_score,
                'new_lot_sizes': new_lot_sizes
            }
            
            self.performance_log.append(scaling_event)
            
            self.logger.info(f"✅ Account upscaled successfully to ${target_amount:.2f}")
            self.logger.info(f"💰 New lot sizes: {new_lot_sizes}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error upscaling account: {e}")
            return False
    
    async def _calculate_scaled_lot_sizes(self, target_balance: float) -> Dict[str, float]:
        """Calculate scaled lot sizes for target balance"""
        try:
            lot_sizes = {}
            risk_percentage = self.config.get('lot_size_calculation', {}).get('risk_percentage', 0.01)
            pip_values = self.config.get('lot_size_calculation', {}).get('pip_values', {})
            
            # Calculate risk amount
            risk_amount = target_balance * risk_percentage
            
            # Calculate lot sizes for each symbol
            for symbol, pip_value in pip_values.items():
                # Standard calculation: risk_amount / (stop_distance * pip_value)
                # Using 50 pip stop distance as standard
                stop_distance_pips = 50
                
                lot_size = risk_amount / (stop_distance_pips * pip_value)
                
                # Round to standard lot sizes
                standard_lots = self.config.get('lot_size_calculation', {}).get('lot_size_steps', 
                    [0.01, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0, 2.0, 3.0, 5.0])
                
                closest_lot = min(standard_lots, key=lambda x: abs(x - lot_size))
                
                # Apply limits
                min_lot = self.config.get('lot_size_calculation', {}).get('minimum_lot_size', 0.01)
                max_lot = self.config.get('lot_size_calculation', {}).get('maximum_lot_size', 5.0)
                
                closest_lot = max(min_lot, min(closest_lot, max_lot))
                
                lot_sizes[symbol] = closest_lot
            
            return lot_sizes
            
        except Exception as e:
            self.logger.error(f"❌ Error calculating scaled lot sizes: {e}")
            return {}
    
    async def _update_scaling_config(self, target_balance: float, new_lot_sizes: Dict[str, float]):
        """Update scaling configuration with new target"""
        try:
            # Update current balance
            self.config['scaling_configuration']['scaling_targets']['current_balance'] = target_balance
            
            # Determine new phase
            new_phase = await self._determine_scaling_phase(target_balance)
            self.current_phase = new_phase
            
            # Update lot size configuration
            if 'lot_size_calculation' not in self.config:
                self.config['lot_size_calculation'] = {}
            
            self.config['lot_size_calculation']['target_balance'] = target_balance
            self.config['lot_size_calculation']['calculated_lot_sizes'] = new_lot_sizes
            self.config['lot_size_calculation']['current_phase'] = new_phase.phase
            
            # Save configuration
            await self._save_config()
            
        except Exception as e:
            self.logger.error(f"❌ Error updating scaling config: {e}")
    
    async def _determine_scaling_phase(self, balance: float) -> ScalingPhase:
        """Determine current scaling phase"""
        try:
            scaling_phases = self.config.get('scaling_configuration', {}).get('scaling_targets', {}).get('scaling_phases', [])
            
            for phase_config in scaling_phases:
                balance_range = phase_config.get('balance_range', [0, 0])
                if balance_range[0] <= balance <= balance_range[1]:
                    return ScalingPhase(
                        phase=phase_config.get('phase', 'Unknown'),
                        balance_range=balance_range,
                        max_position_size=phase_config.get('max_position_size', 0.01),
                        daily_trades_limit=phase_config.get('daily_trades_limit', 5)
                    )
            
            # Default to initial phase
            return ScalingPhase(
                phase='Initial',
                balance_range=[0, 1000],
                max_position_size=0.01,
                daily_trades_limit=5
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error determining scaling phase: {e}")
            return ScalingPhase('Initial', [0, 1000], 0.01, 5)
    
    async def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.info("✅ Scaling configuration saved")
            
        except Exception as e:
            self.logger.error(f"❌ Error saving configuration: {e}")
    
    def get_current_lot_size(self, symbol: str) -> float:
        """Get current lot size for symbol"""
        try:
            lot_sizes = self.config.get('lot_size_calculation', {}).get('calculated_lot_sizes', {})
            return lot_sizes.get(symbol, 0.01)
            
        except Exception as e:
            self.logger.error(f"❌ Error getting lot size for {symbol}: {e}")
            return 0.01
    
    def get_scaling_status(self) -> Dict[str, Any]:
        """Get current scaling status"""
        try:
            return {
                'current_phase': self.current_phase.phase if self.current_phase else 'Unknown',
                'target_balance': self.config.get('lot_size_calculation', {}).get('target_balance', 1000.0),
                'max_position_size': self.current_phase.max_position_size if self.current_phase else 0.01,
                'daily_trades_limit': self.current_phase.daily_trades_limit if self.current_phase else 5,
                'risk_percentage': self.config.get('lot_size_calculation', {}).get('risk_percentage', 0.01),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting scaling status: {e}")
            return {}
    
    def get_performance_log(self) -> List[Dict[str, Any]]:
        """Get performance log"""
        return self.performance_log

# Global scaling manager instance
scaling_manager = ScalingManager()
