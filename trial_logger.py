"""
UOTA Elite v2 - Trial Logger
60-day elite validation phase tracking
"""

# import json  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class WeeklyReport:
    """Weekly performance report"""
    week_number: int
    start_date: str
    end_date: str
    total_smc_setups: int
    executed_trades: int
    accuracy_liquidity_sweeps: float
    accuracy_order_blocks: float
    xauusd_win_loss_ratio: float
    total_profit_loss: float
    skill_score: float

@dataclass
class TrialStats:
    """Trial statistics tracker"""
    trial_start_date: datetime
    current_day: int
    total_days: int
    weekly_reports: List[WeeklyReport]
    cumulative_smc_setups: int
    cumulative_trades: int
    cumulative_profit_loss: float
    current_skill_score: float

class TrialLogger:
    """60-day trial validation logger"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.trial_file = "logs/trial_validation.json"
        self.stats_file = "logs/trial_stats.json"
        
        # Initialize trial data
        self.trial_stats = TrialStats(
            trial_start_date=datetime.now(),
            current_day=1,
            total_days=60,
            weekly_reports=[],
            cumulative_smc_setups=0,
            cumulative_trades=0,
            cumulative_profit_loss=0.0,
            current_skill_score=100.0
        )
        
        # Load existing data if available
        self._load_trial_data()
    
    def _load_trial_data(self):
        """Load existing trial data"""
        try:
            if Path(self.stats_file).exists():
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    # Convert dates back to datetime
                    data['trial_start_date'] = datetime.fromisoformat(data['trial_start_date'])
                    self.trial_stats = TrialStats(**data)
                    self.logger.info("✅ Trial data loaded successfully")
        except Exception as e:
            self.logger.error(f"❌ Error loading trial data: {e}")
    
    def _save_trial_data(self):
        """Save trial data"""
        try:
            # Ensure logs directory exists
            Path("logs").mkdir(exist_ok=True)
            
            # Save stats
            with open(self.stats_file, 'w') as f:
                data = asdict(self.trial_stats)
                # Convert datetime to string for JSON
                data['trial_start_date'] = data['trial_start_date'].isoformat()
                json.dump(data, f, indent=2)
            
            self.logger.info("✅ Trial data saved")
        except Exception as e:
            self.logger.error(f"❌ Error saving trial data: {e}")
    
    def log_smc_setup(self, symbol: str, setup_type: str, confidence: float):
        """Log identified SMC setup"""
        self.trial_stats.cumulative_smc_setups += 1
        self.logger.info(f"🔍 SMC Setup: {symbol} - {setup_type} - Confidence: {confidence:.2%}")
        self._save_trial_data()
    
    def log_trade_execution(self, 
                         symbol: str, 
                         setup_type: str,
                         entry_price: float,
                         exit_price: float,
                         profit_loss: float,
                         was_liquidity_sweep: bool,
                         was_order_block: bool):
        """Log trade execution"""
        self.trial_stats.cumulative_trades += 1
        self.trial_stats.cumulative_profit_loss += profit_loss
        
        self.logger.info(f"""
📈 TRADE EXECUTED:
Symbol: {symbol}
Setup: {setup_type}
Entry: ${entry_price:.5f}
Exit: ${exit_price:.5f}
P&L: ${profit_loss:.2f}
Liquidity Sweep: {'✅' if was_liquidity_sweep else '❌'}
Order Block: {'✅' if was_order_block else '❌'}
""")
        
        self._save_trial_data()
    
    def update_skill_score(self, new_score: float):
        """Update current skill score"""
        self.trial_stats.current_skill_score = new_score
        self.logger.info(f"🎯 Skill Score Updated: {new_score:.1f}%")
        self._save_trial_data()
    
    def generate_weekly_report(self) -> WeeklyReport:
        """Generate weekly performance report"""
        try:
            current_date = datetime.now()
            week_number = self.trial_stats.current_day // 7 + 1
            
            # Calculate week dates
            week_start = self.trial_stats.trial_start_date + timedelta(weeks=week_number-1)
            week_end = week_start + timedelta(days=6)
            
            # For demo purposes, calculate mock metrics
            # In real implementation, these would be calculated from actual trade data
            report = WeeklyReport(
                week_number=week_number,
                start_date=week_start.strftime('%Y-%m-%d'),
                end_date=week_end.strftime('%Y-%m-%d'),
                total_smc_setups=self.trial_stats.cumulative_smc_setups,
                executed_trades=self.trial_stats.cumulative_trades,
                accuracy_liquidity_sweeps=0.85,  # Mock 85%
                accuracy_order_blocks=0.90,      # Mock 90%
                xauusd_win_loss_ratio=1.5,       # Mock 1.5:1
                total_profit_loss=self.trial_stats.cumulative_profit_loss,
                skill_score=self.trial_stats.current_skill_score
            )
            
            # Add to reports
            self.trial_stats.weekly_reports.append(report)
            
            # Log report
            self.logger.info(f"""
╔════════════════════════════════════════════════════════════╗
║              📊 WEEK {week_number} SKILL PERFORMANCE REPORT           ║
╚════════════════════════════════════════════════════════════╝

📅 PERIOD: {report.start_date} to {report.end_date}
🔍 TOTAL SMC SETUPS: {report.total_smc_setups}
📈 EXECUTED TRADES: {report.executed_trades}
🌊 LIQUIDITY SWEEP ACCURACY: {report.accuracy_liquidity_sweeps:.1%}
🎯 ORDER BLOCK ACCURACY: {report.accuracy_order_blocks:.1%}
🥇 XAUUSD WIN/LOSS RATIO: {report.xauusd_win_loss_ratio:.2f}:1
💰 TOTAL P&L: ${report.total_profit_loss:.2f}
🎪 SKILL SCORE: {report.skill_score:.1f}%

📊 PERFORMANCE SUMMARY:
{'✅ EXCELLENT' if report.skill_score >= 95 else '⚠️ NEEDS IMPROVEMENT' if report.skill_score >= 85 else '❌ CRITICAL'}
""")
            
            self._save_trial_data()
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating weekly report: {e}")
            return None
    
    def get_trial_status(self) -> Dict:
        """Get current trial status"""
        days_remaining = self.trial_stats.total_days - self.trial_stats.current_day
        progress = (self.trial_stats.current_day / self.trial_stats.total_days) * 100
        
        return {
            'current_day': self.trial_stats.current_day,
            'total_days': self.trial_stats.total_days,
            'days_remaining': days_remaining,
            'progress_percentage': progress,
            'trial_start_date': self.trial_stats.trial_start_date.strftime('%Y-%m-%d'),
            'current_skill_score': self.trial_stats.current_skill_score,
            'cumulative_smc_setups': self.trial_stats.cumulative_smc_setups,
            'cumulative_trades': self.trial_stats.cumulative_trades,
            'cumulative_profit_loss': self.trial_stats.cumulative_profit_loss
        }
    
    def increment_day(self):
        """Increment trial day"""
        self.trial_stats.current_day += 1
        
        # Check if week completed
        if self.trial_stats.current_day % 7 == 0:
            self.generate_weekly_report()
        
        self._save_trial_data()
    
    def is_trial_complete(self) -> bool:
        """Check if 60-day trial is complete"""
        return self.trial_stats.current_day >= self.trial_stats.total_days

# Global trial logger instance
trial_logger = TrialLogger()
