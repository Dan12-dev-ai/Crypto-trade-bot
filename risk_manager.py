"""
UOTA Elite v2 - Risk Management System
Strict risk enforcement with zero tolerance for violations
"""

# import logging  # Moved to function to avoid circular import
# import asyncio  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
# import numpy  # Moved to function to avoid circular import as np
# import pandas  # Moved to function to avoid circular import as pd
from config # import config  # Moved to function to avoid circular import

class RiskLevel(Enum):
    """Risk severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class TradingStatus(Enum):
    """Trading status flags"""
    TRADING = "trading"
    PAUSED = "paused"
    STOPPED = "stopped"
    EMERGENCY = "emergency"

@dataclass
class RiskMetrics:
    """Current risk metrics"""
    current_balance: float = 0.0
    daily_pnl: float = 0.0
    total_pnl: float = 0.0
    daily_loss: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    open_positions: int = 0
    total_risk: float = 0.0
    leverage_used: float = 0.0
    volatility_score: float = 0.0
    risk_score: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class PositionRisk:
    """Individual position risk data"""
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    risk_amount: float
    leverage: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    trailing_stop: Optional[float] = None
    duration: timedelta = field(default_factory=timedelta)
    
@dataclass
class RiskAlert:
    """Risk alert data"""
    level: RiskLevel
    message: str
    timestamp: datetime
    metrics: RiskMetrics
    action_required: Optional[str] = None

class RiskManager:
    """Strict risk management system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.metrics = RiskMetrics()
        self.positions: Dict[str, PositionRisk] = {}
        self.daily_trades: List[Dict] = []
        self.alerts: List[RiskAlert] = []
        self.trading_status = TradingStatus.TRADING
        self.daily_start_balance = 0.0
        self.peak_balance = 0.0
        self.last_risk_check = datetime.now()
        
        # Risk thresholds from config - HARD CODED FOR MAXIMUM SAFETY
        self.max_risk_per_trade = 0.01  # 1% - NON-NEGOTIABLE
        self.max_daily_loss = 0.05  # 5% - NON-NEGOTIABLE
        self.max_drawdown = 0.20  # 20% - NON-NEGOTIABLE
        self.volatility_threshold = 0.03  # 3% - NON-NEGOTIABLE
        self.max_positions = 5  # NON-NEGOTIABLE
        self.max_leverage = 10.0  # MAXIMUM ALLOWED
        
        # Engine-level hard stops that cannot be overridden
        self.EMERGENCY_STOP_DRAWDOWN = 0.25  # 25% - Absolute maximum
        self.CRITICAL_DAILY_LOSS = 0.08  # 8% - Critical daily stop
        self.MAX_CORRELATION_EXPOSURE = 0.15  # 15% max in correlated assets
        self.FORCE_CLOSE_THRESHOLD = 0.18  # 18% - Force close all positions
        
        # Circuit breakers
        self.circuit_breaker_triggered = False
        self.circuit_breaker_reason = None
        self.last_circuit_breaker_reset = datetime.now()
        self.circuit_breaker_cooldown = 3600  # 1 hour cooldown
        
    async def initialize(self, starting_balance: float) -> None:
        """Initialize risk manager with starting balance"""
        try:
            self.metrics.current_balance = starting_balance
            self.daily_start_balance = starting_balance
            self.peak_balance = starting_balance
            self.logger.info(f"Risk manager initialized with balance: ${starting_balance:.2f}")
        except Exception as e:
            self.logger.error(f"Error initializing risk manager: {e}")
            raise
            
    def calculate_position_size(self, 
                             entry_price: float, 
                             stop_loss_price: float,
                             volatility: float = 0.0) -> Tuple[float, float]:
        """
        Calculate position size based on strict risk rules
        
        Returns:
            Tuple[position_size, risk_amount]
        """
        try:
            # Validate inputs
            if entry_price <= 0 or stop_loss_price <= 0:
                raise ValueError("Invalid prices for position sizing")
                
            # Calculate stop distance in percentage
            if stop_loss_price > entry_price:  # Long position
                stop_distance_pct = (stop_loss_price - entry_price) / entry_price
            else:  # Short position
                stop_distance_pct = (entry_price - stop_loss_price) / entry_price
                
            # Base risk amount (1% of current balance)
            risk_amount = self.metrics.current_balance * self.max_risk_per_trade
            
            # Volatility adjustment - reduce size in high volatility
            if volatility > self.volatility_threshold:
                volatility_factor = self.volatility_threshold / volatility
                risk_amount *= volatility_factor
                self.logger.warning(f"High volatility detected ({volatility:.2%}), reducing position size by factor {volatility_factor:.2f}")
                
            # Calculate position size
            position_size = risk_amount / (stop_distance_pct * entry_price)
            
            # Apply leverage limits
            max_position_value = self.metrics.current_balance * self.max_leverage
            position_value = position_size * entry_price
            
            if position_value > max_position_value:
                position_size = max_position_value / entry_price
                actual_risk = position_size * stop_distance_pct * entry_price
                self.logger.warning(f"Position size reduced due to leverage limit. New risk: ${actual_risk:.2f}")
                
            # Minimum trade size check
            if position_size * entry_price < config.trading.min_trade_size:
                return 0.0, 0.0
                
            return position_size, risk_amount
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0, 0.0
            
    def validate_trade(self, 
                      symbol: str, 
                      side: str, 
                      size: float, 
                      entry_price: float,
                      stop_loss: float,
                      leverage: float = 1.0) -> Tuple[bool, str]:
        """
        Validate trade against all risk rules
        
        Returns:
            Tuple[is_valid, reason]
        """
        try:
            # Check trading status
            if self.trading_status in [TradingStatus.STOPPED, TradingStatus.EMERGENCY]:
                return False, f"Trading is {self.trading_status.value}"
                
            if self.trading_status == TradingStatus.PAUSED:
                if self.metrics.daily_loss >= self.max_daily_loss * 0.8:  # 80% of daily limit
                    return False, "Daily loss limit approaching"
                    
            # Check position limits
            if len(self.positions) >= self.max_positions:
                return False, f"Maximum positions ({self.max_positions}) reached"
                
            # Check leverage
            if leverage > self.max_leverage:
                return False, f"Leverage ({leverage}x) exceeds maximum ({self.max_leverage}x)"
                
            # Calculate risk
            position_value = size * entry_price
            risk_amount = self.calculate_risk_amount(side, size, entry_price, stop_loss)
            
            # Check per-trade risk limit
            if risk_amount > self.metrics.current_balance * self.max_risk_per_trade:
                return False, f"Trade risk (${risk_amount:.2f}) exceeds maximum ({self.metrics.current_balance * self.max_risk_per_trade:.2f})"
                
            # Check total exposure
            total_exposure = sum(pos.size * pos.entry_price for pos in self.positions.values())
            if total_exposure + position_value > self.metrics.current_balance * self.max_leverage:
                return False, "Total exposure exceeds leverage limit"
                
            # Check daily loss limit
            if self.metrics.daily_loss >= self.max_daily_loss:
                return False, f"Daily loss limit ({self.max_daily_loss:.1%}) reached"
                
            # Check drawdown limit
            if self.metrics.current_drawdown >= self.max_drawdown:
                return False, f"Maximum drawdown ({self.max_drawdown:.1%}) reached"
                
            # ENGINE-LEVEL CRITICAL VALIDATIONS (Cannot be overridden)
            return self._engine_level_validation(side, size, entry_price, stop_loss, leverage)
            
        except Exception as e:
            self.logger.error(f"Error validating trade: {e}")
            return False, f"Validation error: {str(e)}"
            
    def _engine_level_validation(self, side: str, size: float, entry_price: float, 
                                stop_loss: float, leverage: float) -> Tuple[bool, str]:
        """Engine-level validation that cannot be overridden by AI decisions"""
        try:
            # Check circuit breaker
            if self.circuit_breaker_triggered:
                return False, f"CIRCUIT BREAKER ACTIVE: {self.circuit_breaker_reason}"
                
            # Check emergency drawdown - IMMEDIATE STOP
            if self.metrics.current_drawdown >= self.EMERGENCY_STOP_DRAWDOWN:
                self._trigger_circuit_breaker("EMERGENCY_DRAWDOWN", f"Drawdown reached {self.metrics.current_drawdown:.1%}")
                return False, "EMERGENCY STOP: Critical drawdown exceeded"
                
            # Check critical daily loss
            if self.metrics.daily_loss >= self.CRITICAL_DAILY_LOSS:
                self._trigger_circuit_breaker("CRITICAL_DAILY_LOSS", f"Daily loss reached {self.metrics.daily_loss:.1%}")
                return False, "EMERGENCY STOP: Critical daily loss exceeded"
                
            # Check force close threshold
            if self.metrics.current_drawdown >= self.FORCE_CLOSE_THRESHOLD:
                self._trigger_emergency_close("FORCE_CLOSE_THRESHOLD", f"Drawdown {self.metrics.current_drawdown:.1%} exceeded force close threshold")
                return False, "EMERGENCY: All positions will be force closed"
                
            # Validate leverage is within absolute maximum
            if leverage > 20.0:  # Absolute maximum regardless of config
                return False, f"ABSOLUTE LEVERAGE LIMIT: {leverage}x exceeds maximum allowed 20x"
                
            # Validate position size against absolute maximum
            max_position_value = self.metrics.current_balance * 0.5  # 50% max per position
            position_value = size * entry_price
            if position_value > max_position_value:
                return False, f"POSITION SIZE LIMIT: ${position_value:.2f} exceeds maximum ${max_position_value:.2f}"
                
            # Check correlation exposure (simplified)
            correlation_risk = self._calculate_correlation_risk(side, size)
            if correlation_risk > self.MAX_CORRELATION_EXPOSURE:
                return False, f"CORRELATION RISK: {correlation_risk:.1%} exceeds maximum {self.MAX_CORRELATION_EXPOSURE:.1%}"
                
            return True, "Trade validated by engine-level checks"
            
        except Exception as e:
            self.logger.error(f"Error in engine-level validation: {e}")
            return False, f"Engine validation error: {str(e)}"
            
    def _trigger_circuit_breaker(self, reason: str, details: str):
        """Trigger circuit breaker to stop all trading"""
        self.circuit_breaker_triggered = True
        self.circuit_breaker_reason = f"{reason}: {details}"
        self.trading_status = TradingStatus.EMERGENCY
        
        self.logger.critical(f"🚨 CIRCUIT BREAKER TRIGGERED: {self.circuit_breaker_reason}")
        
        # Log to system
        try:
            from database # # # import database  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import, SystemLog
            asyncio.create_task(database.save_log(SystemLog(
                level="CRITICAL",
                component="risk_manager",
                message=f"Circuit breaker triggered: {reason}",
                data={"reason": reason, "details": details, "timestamp": datetime.now().isoformat()}
            )))
        except:
            pass
            
    def _trigger_emergency_close(self, reason: str, details: str):
        """Trigger emergency close of all positions"""
        self.trading_status = TradingStatus.EMERGENCY
        
        self.logger.critical(f"🚨 EMERGENCY CLOSE TRIGGERED: {reason} - {details}")
        
        # This would trigger the supervisor to close all positions
        try:
            from database # # # import database  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import, SystemLog
            asyncio.create_task(database.save_log(SystemLog(
                level="CRITICAL",
                component="risk_manager",
                message=f"Emergency close triggered: {reason}",
                data={"reason": reason, "details": details, "timestamp": datetime.now().isoformat()}
            )))
        except:
            pass
            
    def _calculate_correlation_risk(self, side: str, size: float) -> float:
        """Calculate correlation risk for new position"""
        try:
            # Simplified correlation calculation
            # In production, this would use actual correlation matrices
            correlated_symbols = {
                'BTC': ['ETH', 'BNB', 'SOL'],
                'ETH': ['BTC', 'BNB', 'ADA'],
                'ADA': ['ETH', 'DOT'],
                'DOT': ['ADA', 'LINK']
            }
            
            total_correlated_exposure = 0.0
            
            for symbol, position in self.positions.items():
                # Simple correlation check
                base_symbol = symbol.split('/')[0]
                for correlated_group in correlated_symbols.values():
                    if base_symbol in correlated_group:
                        total_correlated_exposure += position.size * position.entry_price
                        
            # Add new position to correlated exposure
            new_position_exposure = size * 50000  # Assuming $50k price for calculation
            
            return (total_correlated_exposure + new_position_exposure) / self.metrics.current_balance
            
        except Exception as e:
            self.logger.error(f"Error calculating correlation risk: {e}")
            return 0.0
            
    async def reset_circuit_breaker(self):
        """Reset circuit breaker after cooldown period"""
        try:
            if not self.circuit_breaker_triggered:
                return
                
            time_since_trigger = (datetime.now() - self.last_circuit_breaker_reset).total_seconds()
            
            if time_since_trigger >= self.circuit_breaker_cooldown:
                self.circuit_breaker_triggered = False
                self.circuit_breaker_reason = None
                self.trading_status = TradingStatus.TRADING
                self.last_circuit_breaker_reset = datetime.now()
                
                self.logger.info("✅ Circuit breaker reset - trading resumed")
                
                # Log reset
                try:
                    from database # # # import database  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import, SystemLog
                    await database.save_log(SystemLog(
                        level="INFO",
                        component="risk_manager",
                        message="Circuit breaker reset",
                        data={"timestamp": datetime.now().isoformat()}
                    ))
                except:
                    pass
            else:
                remaining_time = self.circuit_breaker_cooldown - time_since_trigger
                self.logger.warning(f"Circuit breaker cooldown: {remaining_time:.0f} seconds remaining")
                
        except Exception as e:
            self.logger.error(f"Error resetting circuit breaker: {e}")
            
    def get_engine_status(self) -> Dict[str, Any]:
        """Get current engine-level risk status"""
        return {
            'circuit_breaker_active': self.circuit_breaker_triggered,
            'circuit_breaker_reason': self.circuit_breaker_reason,
            'trading_status': self.trading_status.value,
            'emergency_drawdown': self.metrics.current_drawdown >= self.EMERGENCY_STOP_DRAWDOWN,
            'critical_daily_loss': self.metrics.daily_loss >= self.CRITICAL_DAILY_LOSS,
            'force_close_active': self.metrics.current_drawdown >= self.FORCE_CLOSE_THRESHOLD,
            'engine_limits': {
                'max_risk_per_trade': self.max_risk_per_trade,
                'max_daily_loss': self.max_daily_loss,
                'max_drawdown': self.max_drawdown,
                'emergency_stop_drawdown': self.EMERGENCY_STOP_DRAWDOWN,
                'critical_daily_loss': self.CRITICAL_DAILY_LOSS,
                'force_close_threshold': self.FORCE_CLOSE_THRESHOLD
            }
        }
            
    def calculate_risk_amount(self, side: str, size: float, entry_price: float, stop_loss: float) -> float:
        """Calculate risk amount for a position"""
        try:
            if side.lower() == 'long':
                risk_per_unit = max(0, entry_price - stop_loss)
            else:
                risk_per_unit = max(0, stop_loss - entry_price)
                
            return size * risk_per_unit
        except Exception as e:
            self.logger.error(f"Error calculating risk amount: {e}")
            return float('inf')
            
    async def update_position(self, 
                            symbol: str, 
                            side: str, 
                            size: float, 
                            current_price: float,
                            entry_price: Optional[float] = None,
                            stop_loss: Optional[float] = None,
                            take_profit: Optional[float] = None) -> None:
        """Update or add position risk data"""
        try:
            now = datetime.now()
            
            if symbol in self.positions:
                # Update existing position
                position = self.positions[symbol]
                position.current_price = current_price
                position.unrealized_pnl = self.calculate_unrealized_pnl(position)
                position.duration = now - position.entry_time if hasattr(position, 'entry_time') else timedelta()
                
                # Update stop loss/take profit if provided
                if stop_loss:
                    position.stop_loss = stop_loss
                if take_profit:
                    position.take_profit = take_profit
            else:
                # New position
                if entry_price is None:
                    entry_price = current_price
                    
                unrealized_pnl = self.calculate_unrealized_pnl_manual(side, size, entry_price, current_price)
                risk_amount = self.calculate_risk_amount(side, size, entry_price, stop_loss or current_price * 0.95)
                
                self.positions[symbol] = PositionRisk(
                    symbol=symbol,
                    side=side,
                    size=size,
                    entry_price=entry_price,
                    current_price=current_price,
                    unrealized_pnl=unrealized_pnl,
                    risk_amount=risk_amount,
                    leverage=self.max_leverage,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    entry_time=now
                )
                
            # Update overall metrics
            await self.update_metrics()
            
        except Exception as e:
            self.logger.error(f"Error updating position {symbol}: {e}")
            
    def calculate_unrealized_pnl(self, position: PositionRisk) -> float:
        """Calculate unrealized P&L for a position"""
        try:
            if position.side.lower() == 'long':
                return position.size * (position.current_price - position.entry_price)
            else:
                return position.size * (position.entry_price - position.current_price)
        except Exception as e:
            self.logger.error(f"Error calculating unrealized P&L: {e}")
            return 0.0
            
    def calculate_unrealized_pnl_manual(self, side: str, size: float, entry_price: float, current_price: float) -> float:
        """Calculate unrealized P&L manually"""
        try:
            if side.lower() == 'long':
                return size * (current_price - entry_price)
            else:
                return size * (entry_price - current_price)
        except Exception as e:
            self.logger.error(f"Error calculating manual unrealized P&L: {e}")
            return 0.0
            
    async def close_position(self, symbol: str, exit_price: float, commission: float = 0.0) -> float:
        """Close position and update metrics"""
        try:
            if symbol not in self.positions:
                self.logger.warning(f"Position {symbol} not found for closing")
                return 0.0
                
            position = self.positions[symbol]
            realized_pnl = self.calculate_unrealized_pnl_manual(
                position.side, position.size, position.entry_price, exit_price
            )
            
            # Subtract commission
            realized_pnl -= commission
            
            # Update metrics
            self.metrics.total_pnl += realized_pnl
            self.metrics.daily_pnl += realized_pnl
            
            if realized_pnl < 0:
                self.metrics.daily_loss += abs(realized_pnl)
                
            # Remove position
            del self.positions[symbol]
            
            # Log trade
            trade_record = {
                'symbol': symbol,
                'side': position.side,
                'size': position.size,
                'entry_price': position.entry_price,
                'exit_price': exit_price,
                'pnl': realized_pnl,
                'commission': commission,
                'duration': position.duration,
                'timestamp': datetime.now()
            }
            self.daily_trades.append(trade_record)
            
            # Update overall metrics
            await self.update_metrics()
            
            self.logger.info(f"Closed position {symbol}: P&L ${realized_pnl:.2f}")
            return realized_pnl
            
        except Exception as e:
            self.logger.error(f"Error closing position {symbol}: {e}")
            return 0.0
            
    async def update_metrics(self) -> None:
        """Update all risk metrics"""
        try:
            # Calculate total unrealized P&L
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            
            # Update current balance (starting + realized + unrealized)
            self.metrics.current_balance = (
                self.daily_start_balance + 
                self.metrics.total_pnl + 
                total_unrealized_pnl
            )
            
            # Update peak balance for drawdown calculation
            if self.metrics.current_balance > self.peak_balance:
                self.peak_balance = self.metrics.current_balance
                
            # Calculate current drawdown
            if self.peak_balance > 0:
                self.metrics.current_drawdown = (self.peak_balance - self.metrics.current_balance) / self.peak_balance
                self.metrics.max_drawdown = max(self.metrics.max_drawdown, self.metrics.current_drawdown)
                
            # Update position counts
            self.metrics.open_positions = len(self.positions)
            
            # Calculate total risk
            self.metrics.total_risk = sum(pos.risk_amount for pos in self.positions.values())
            
            # Calculate leverage used
            total_position_value = sum(pos.size * pos.current_price for pos in self.positions.values())
            if self.metrics.current_balance > 0:
                self.metrics.leverage_used = total_position_value / self.metrics.current_balance
                
            # Update timestamp
            self.metrics.last_updated = datetime.now()
            
            # Check for risk alerts
            await self.check_risk_alerts()
            
        except Exception as e:
            self.logger.error(f"Error updating metrics: {e}")
            
    async def check_risk_alerts(self) -> None:
        """Check for risk conditions and generate alerts"""
        try:
            now = datetime.now()
            
            # Daily loss warning
            if self.metrics.daily_loss >= self.max_daily_loss * 0.8:
                await self.create_alert(
                    RiskLevel.HIGH,
                    f"Daily loss approaching limit: {self.metrics.daily_loss:.1%} of {self.max_daily_loss:.1%}",
                    "Consider reducing position sizes or pausing trading"
                )
                
            # Daily limit reached
            if self.metrics.daily_loss >= self.max_daily_loss:
                self.trading_status = TradingStatus.PAUSED
                await self.create_alert(
                    RiskLevel.CRITICAL,
                    f"Daily loss limit reached: {self.metrics.daily_loss:.1%}",
                    "Trading paused until next day"
                )
                
            # Drawdown warning
            if self.metrics.current_drawdown >= self.max_drawdown * 0.8:
                await self.create_alert(
                    RiskLevel.HIGH,
                    f"Drawdown approaching limit: {self.metrics.current_drawdown:.1%} of {self.max_drawdown:.1%}",
                    "Review risk management strategy"
                )
                
            # Drawdown limit reached
            if self.metrics.current_drawdown >= self.max_drawdown:
                self.trading_status = TradingStatus.STOPPED
                await self.create_alert(
                    RiskLevel.EMERGENCY,
                    f"Maximum drawdown reached: {self.metrics.current_drawdown:.1%}",
                    "Trading stopped - manual intervention required"
                )
                
            # Leverage warning
            if self.metrics.leverage_used >= self.max_leverage * 0.9:
                await self.create_alert(
                    RiskLevel.MEDIUM,
                    f"Leverage usage high: {self.metrics.leverage_used:.1f}x of {self.max_leverage:.1f}x",
                    "Monitor total exposure"
                )
                
        except Exception as e:
            self.logger.error(f"Error checking risk alerts: {e}")
            
    async def create_alert(self, level: RiskLevel, message: str, action_required: Optional[str] = None) -> None:
        """Create and log risk alert"""
        try:
            alert = RiskAlert(
                level=level,
                message=message,
                timestamp=datetime.now(),
                metrics=self.metrics,
                action_required=action_required
            )
            
            self.alerts.append(alert)
            
            # Log alert
            log_level = {
                RiskLevel.LOW: logging.INFO,
                RiskLevel.MEDIUM: logging.WARNING,
                RiskLevel.HIGH: logging.ERROR,
                RiskLevel.CRITICAL: logging.CRITICAL,
                RiskLevel.EMERGENCY: logging.CRITICAL
            }.get(level, logging.INFO)
            
            self.logger.log(log_level, f"[{level.value.upper()}] {message}")
            
            # Keep only last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
                
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            
    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk summary"""
        return {
            'trading_status': self.trading_status.value,
            'current_balance': self.metrics.current_balance,
            'daily_pnl': self.metrics.daily_pnl,
            'total_pnl': self.metrics.total_pnl,
            'daily_loss': self.metrics.daily_loss,
            'daily_loss_pct': self.metrics.daily_loss / max(self.daily_start_balance, 1),
            'current_drawdown': self.metrics.current_drawdown,
            'max_drawdown': self.metrics.max_drawdown,
            'open_positions': self.metrics.open_positions,
            'total_risk': self.metrics.total_risk,
            'leverage_used': self.metrics.leverage_used,
            'risk_score': self.calculate_risk_score(),
            'last_updated': self.metrics.last_updated.isoformat()
        }
        
    def calculate_risk_score(self) -> float:
        """Calculate overall risk score (0-100)"""
        try:
            score = 0
            
            # Daily loss component (30%)
            score += (self.metrics.daily_loss / self.max_daily_loss) * 30
            
            # Drawdown component (30%)
            score += (self.metrics.current_drawdown / self.max_drawdown) * 30
            
            # Leverage component (20%)
            score += (self.metrics.leverage_used / self.max_leverage) * 20
            
            # Position count component (10%)
            score += (self.metrics.open_positions / self.max_positions) * 10
            
            # Volatility component (10%)
            score += min(self.metrics.volatility_score / self.volatility_threshold, 1.0) * 10
            
            return min(score, 100.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating risk score: {e}")
            return 0.0
            
    async def reset_daily(self) -> None:
        """Reset daily metrics at start of new day"""
        try:
            self.daily_start_balance = self.metrics.current_balance
            self.metrics.daily_pnl = 0.0
            self.metrics.daily_loss = 0.0
            self.daily_trades.clear()
            
            # Resume trading if paused due to daily loss
            if self.trading_status == TradingStatus.PAUSED:
                self.trading_status = TradingStatus.TRADING
                
            self.logger.info("Daily metrics reset")
            
        except Exception as e:
            self.logger.error(f"Error resetting daily metrics: {e}")
            
    def pause_trading(self, reason: str = "Manual pause") -> None:
        """Manually pause trading"""
        self.trading_status = TradingStatus.PAUSED
        self.logger.info(f"Trading paused: {reason}")
        
    def resume_trading(self) -> None:
        """Resume trading"""
        if self.trading_status != TradingStatus.EMERGENCY:
            self.trading_status = TradingStatus.TRADING
            self.logger.info("Trading resumed")
            
    def emergency_stop(self, reason: str = "Emergency stop") -> None:
        """Emergency stop all trading"""
        self.trading_status = TradingStatus.EMERGENCY
        self.logger.critical(f"Emergency stop activated: {reason}")

# Global risk manager instance
risk_manager = RiskManager()

if __name__ == "__main__":
    # Test risk manager
    async def test_risk_manager():
        rm = RiskManager()
        await rm.initialize(1000.0)
        
        # Test position sizing
        size, risk = rm.calculate_position_size(100.0, 95.0)
        print(f"Position size: {size:.2f}, Risk: ${risk:.2f}")
        
        # Test trade validation
        valid, reason = rm.validate_trade("BTC/USDT", "long", 1.0, 100.0, 95.0)
        print(f"Trade valid: {valid}, Reason: {reason}")
        
        # Print risk summary
        print(rm.get_risk_summary())
        
    asyncio.run(test_risk_manager())
