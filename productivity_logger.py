"""
UOTA Elite v2 - 30-Day Productivity Logger
Tracks agent skill score separate from profit performance
"""

# import json  # Moved to function to avoid circular import
# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
# import os  # Moved to function to avoid circular import

class SkillLevel(Enum):
    """Skill level classifications"""
    ELITE = "elite"
    PROFESSIONAL = "professional"
    COMPETENT = "competent"
    DEVELOPING = "developing"
    CRITICAL = "critical"

@dataclass
class DailyPerformance:
    """Daily performance metrics"""
    date: datetime
    skill_score: float
    setups_analyzed: int
    valid_setups: int
    trades_executed: int
    winning_trades: int
    losing_trades: int
    profit_loss: float
    rule_violations: int
    reasoning_quality: float

@dataclass
class SkillAlert:
    """Skill performance alert"""
    timestamp: datetime
    alert_type: str
    skill_score: float
    message: str
    action_required: str

class ProductivityLogger:
    """30-Day Productivity and Skill Tracking System"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.log_file = "productivity_log.json"
        self.alert_file = "skill_alerts.json"
        
        # Performance tracking
        self.daily_performances = []
        self.skill_alerts = []
        self.current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Skill thresholds
        self.skill_thresholds = {
            'elite': 95.0,
            'professional': 85.0,
            'competent': 75.0,
            'developing': 65.0,
            'critical': 50.0
        }
        
        # Load existing data
        self._load_performance_data()
        
        # Start monitoring
        self.is_monitoring = False
        
    def _load_performance_data(self):
        """Load existing performance data"""
        try:
            # Load daily performances
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.daily_performances = [
                        DailyPerformance(
                            date=datetime.strptime(p['date'], '%Y-%m-%d %H:%M:%S'),
                            skill_score=p['skill_score'],
                            setups_analyzed=p['setups_analyzed'],
                            valid_setups=p['valid_setups'],
                            trades_executed=p['trades_executed'],
                            winning_trades=p['winning_trades'],
                            losing_trades=p['losing_trades'],
                            profit_loss=p['profit_loss'],
                            rule_violations=p['rule_violations'],
                            reasoning_quality=p['reasoning_quality']
                        )
                        for p in data.get('daily_performances', [])
                    ]
                self.logger.info(f"✅ Loaded {len(self.daily_performances)} daily performance records")
            
            # Load skill alerts
            if os.path.exists(self.alert_file):
                with open(self.alert_file, 'r') as f:
                    data = json.load(f)
                    self.skill_alerts = [
                        SkillAlert(
                            timestamp=datetime.strptime(a['timestamp'], '%Y-%m-%d %H:%M:%S'),
                            alert_type=a['alert_type'],
                            skill_score=a['skill_score'],
                            message=a['message'],
                            action_required=a['action_required']
                        )
                        for a in data.get('skill_alerts', [])
                    ]
                self.logger.info(f"✅ Loaded {len(self.skill_alerts)} skill alerts")
                
        except Exception as e:
            self.logger.error(f"❌ Error loading performance data: {e}")
    
    async def start_monitoring(self):
        """Start 30-day productivity monitoring"""
        try:
            self.is_monitoring = True
            self.logger.info("📊 Starting 30-Day Productivity Monitoring...")
            
            # Monitor daily performance
            while self.is_monitoring:
                await self._daily_performance_check()
                await asyncio.sleep(3600)  # Check every hour
                
        except Exception as e:
            self.logger.error(f"❌ Error in productivity monitoring: {e}")
    
    async def _daily_performance_check(self):
        """Check daily performance and update metrics"""
        try:
            now = datetime.now()
            
            # Check if we need to reset for new day
            if now.hour == 0 and now.minute < 5:  # First 5 minutes of day
                await self._reset_daily_metrics()
            
            # Get current skill score
            from smc_logic_gate # import smc_logic_gate  # Moved to function to avoid circular import
            current_skill_score = smc_logic_gate.get_skill_score()
            
            # Check for skill alerts
            await self._check_skill_alerts(current_skill_score)
            
            # Check if we need to stop trading
            if current_skill_score < self.skill_thresholds['critical']:
                await self._emergency_stop_trading()
                
        except Exception as e:
            self.logger.error(f"❌ Error in daily performance check: {e}")
    
    async def _check_skill_alerts(self, skill_score: float):
        """Check for skill performance alerts"""
        try:
            # Get current skill level
            skill_level = self._get_skill_level(skill_score)
            
            # Check for alert conditions
            if skill_score < self.skill_thresholds['critical']:
                await self._create_skill_alert(
                    alert_type="CRITICAL_SKILL_DROP",
                    skill_score=skill_score,
                    message=f"Skill score critically low: {skill_score:.1f}%",
                    action_required="IMMEDIATE_STOP_TRADING"
                )
                
            elif skill_score < self.skill_thresholds['developing']:
                await self._create_skill_alert(
                    alert_type="SKILL_DEGRADATION",
                    skill_score=skill_score,
                    message=f"Skill score degraded: {skill_score:.1f}%",
                    action_required="REDUCE_POSITION_SIZES"
                )
                
            elif skill_score < self.skill_thresholds['competent']:
                await self._create_skill_alert(
                    alert_type="SKILL_WARNING",
                    skill_score=skill_score,
                    message=f"Skill score warning: {skill_score:.1f}%",
                    action_required="REVIEW_SETUP_QUALITY"
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error checking skill alerts: {e}")
    
    async def _create_skill_alert(self, alert_type: str, skill_score: float, message: str, action_required: str):
        """Create skill performance alert"""
        try:
            # Check if we already have a recent alert of this type
            recent_alerts = [a for a in self.skill_alerts if 
                           a.alert_type == alert_type and 
                           (datetime.now() - a.timestamp).total_seconds() < 3600]  # 1 hour
            
            if recent_alerts:
                return  # Skip duplicate alerts
            
            # Create new alert
            alert = SkillAlert(
                timestamp=datetime.now(),
                alert_type=alert_type,
                skill_score=skill_score,
                message=message,
                action_required=action_required
            )
            
            self.skill_alerts.append(alert)
            
            # Log alert
            self.logger.warning(f"🚨 SKILL ALERT: {message}")
            self.logger.warning(f"🎯 Action Required: {action_required}")
            
            # Save alerts
            await self._save_alerts()
            
            # Execute action if critical
            if action_required == "IMMEDIATE_STOP_TRADING":
                await self._emergency_stop_trading()
                
        except Exception as e:
            self.logger.error(f"❌ Error creating skill alert: {e}")
    
    async def _emergency_stop_trading(self):
        """Emergency stop trading due to skill degradation"""
        try:
            self.logger.error("🚨 EMERGENCY STOP: Skill score below 95% - Trading halted")
            
            # Stop any active trading
            # This would integrate with the main trading system
            # For now, just log the emergency stop
            
            # Send terminal alert
            print("\n" + "="*60)
            print("🚨 UOTA ELITE v2 - EMERGENCY TRADING HALT")
            print("="*60)
            print(f"⚠️  Skill Score Below 95% Threshold")
            print(f"🎯 Action: Trading Automatically Stopped")
            print(f"📊 Review Required: Setup Quality Analysis")
            print(f"🔧 Manual Intervention Needed")
            print("="*60)
            print()
            
        except Exception as e:
            self.logger.error(f"❌ Error in emergency stop: {e}")
    
    async def log_daily_performance(self,
                                  skill_score: float,
                                  setups_analyzed: int,
                                  valid_setups: int,
                                  trades_executed: int,
                                  winning_trades: int,
                                  losing_trades: int,
                                  profit_loss: float,
                                  rule_violations: int = 0,
                                  reasoning_quality: float = 0.0):
        """Log daily performance metrics"""
        try:
            # Check if we already have today's performance
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            existing_performance = next((p for p in self.daily_performances if p.date.date() == today.date()), None)
            
            if existing_performance:
                # Update existing performance
                existing_performance.skill_score = skill_score
                existing_performance.setups_analyzed += setups_analyzed
                existing_performance.valid_setups += valid_setups
                existing_performance.trades_executed += trades_executed
                existing_performance.winning_trades += winning_trades
                existing_performance.losing_trades += losing_trades
                existing_performance.profit_loss += profit_loss
                existing_performance.rule_violations += rule_violations
                existing_performance.reasoning_quality = reasoning_quality
            else:
                # Create new performance record
                performance = DailyPerformance(
                    date=today,
                    skill_score=skill_score,
                    setups_analyzed=setups_analyzed,
                    valid_setups=valid_setups,
                    trades_executed=trades_executed,
                    winning_trades=winning_trades,
                    losing_trades=losing_trades,
                    profit_loss=profit_loss,
                    rule_violations=rule_violations,
                    reasoning_quality=reasoning_quality
                )
                self.daily_performances.append(performance)
            
            # Save performance data
            await self._save_performance_data()
            
            # Keep only last 30 days
            await self._cleanup_old_data()
            
            self.logger.info(f"📊 Daily performance logged: Skill={skill_score:.1f}% | Trades={trades_executed} | P&L=${profit_loss:.2f}")
            
        except Exception as e:
            self.logger.error(f"❌ Error logging daily performance: {e}")
    
    async def _save_performance_data(self):
        """Save performance data to file"""
        try:
            data = {
                'daily_performances': [
                    {
                        'date': p.date.strftime('%Y-%m-%d %H:%M:%S'),
                        'skill_score': p.skill_score,
                        'setups_analyzed': p.setups_analyzed,
                        'valid_setups': p.valid_setups,
                        'trades_executed': p.trades_executed,
                        'winning_trades': p.winning_trades,
                        'losing_trades': p.losing_trades,
                        'profit_loss': p.profit_loss,
                        'rule_violations': p.rule_violations,
                        'reasoning_quality': p.reasoning_quality
                    }
                    for p in self.daily_performances
                ]
            }
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving performance data: {e}")
    
    async def _save_alerts(self):
        """Save skill alerts to file"""
        try:
            data = {
                'skill_alerts': [
                    {
                        'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        'alert_type': a.alert_type,
                        'skill_score': a.skill_score,
                        'message': a.message,
                        'action_required': a.action_required
                    }
                    for a in self.skill_alerts
                ]
            }
            
            with open(self.alert_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"❌ Error saving alerts: {e}")
    
    async def _cleanup_old_data(self):
        """Keep only last 30 days of data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)
            
            # Clean daily performances
            self.daily_performances = [p for p in self.daily_performances if p.date >= cutoff_date]
            
            # Clean alerts
            self.skill_alerts = [a for a in self.skill_alerts if a.timestamp >= cutoff_date]
            
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old data: {e}")
    
    def _get_skill_level(self, skill_score: float) -> SkillLevel:
        """Get skill level based on score"""
        if skill_score >= self.skill_thresholds['elite']:
            return SkillLevel.ELITE
        elif skill_score >= self.skill_thresholds['professional']:
            return SkillLevel.PROFESSIONAL
        elif skill_score >= self.skill_thresholds['competent']:
            return SkillLevel.COMPETENT
        elif skill_score >= self.skill_thresholds['developing']:
            return SkillLevel.DEVELOPING
        else:
            return SkillLevel.CRITICAL
    
    def get_30_day_summary(self) -> Dict[str, Any]:
        """Get 30-day performance summary"""
        try:
            if not self.daily_performances:
                return {'message': 'No performance data available'}
            
            # Calculate metrics
            total_days = len(self.daily_performances)
            avg_skill_score = sum(p.skill_score for p in self.daily_performances) / total_days
            total_setups = sum(p.setups_analyzed for p in self.daily_performances)
            total_valid = sum(p.valid_setups for p in self.daily_performances)
            total_trades = sum(p.trades_executed for p in self.daily_performances)
            total_wins = sum(p.winning_trades for p in self.daily_performances)
            total_losses = sum(p.losing_trades for p in self.daily_performances)
            total_pnl = sum(p.profit_loss for p in self.daily_performances)
            
            # Calculate rates
            setup_quality = total_valid / max(total_setups, 1)
            win_rate = total_wins / max(total_trades, 1)
            daily_avg_trades = total_trades / total_days
            
            # Get current skill level
            current_skill = self.daily_performances[-1].skill_score if self.daily_performances else 0
            skill_level = self._get_skill_level(current_skill)
            
            return {
                'period_days': total_days,
                'current_skill_score': current_skill,
                'skill_level': skill_level.value,
                'average_skill_score': avg_skill_score,
                'total_setups_analyzed': total_setups,
                'total_valid_setups': total_valid,
                'setup_quality_ratio': setup_quality,
                'total_trades_executed': total_trades,
                'total_winning_trades': total_wins,
                'total_losing_trades': total_losses,
                'win_rate': win_rate,
                'total_profit_loss': total_pnl,
                'daily_average_trades': daily_avg_trades,
                'recent_alerts': len([a for a in self.skill_alerts if (datetime.now() - a.timestamp).total_seconds() < 86400]),
                'skill_threshold_met': current_skill >= self.skill_thresholds['elite'],
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting 30-day summary: {e}")
            return {'error': str(e)}
    
    def stop_monitoring(self):
        """Stop productivity monitoring"""
        self.is_monitoring = False
        self.logger.info("📊 Productivity monitoring stopped")

# Global productivity logger instance
productivity_logger = ProductivityLogger()
