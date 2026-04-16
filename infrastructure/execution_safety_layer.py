"""
UOTA Elite v2 - Execution Safety Layer
Adds safeguards around MT5 execution without touching trading logic
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
# import aiofiles  # Moved to function to avoid circular import

class ExecutionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class SafetyLevel(Enum):
    SAFE = "safe"
    WARNING = "warning"
    RISKY = "risky"
    CRITICAL = "critical"

@dataclass
class ExecutionRequest:
    """Execution request information"""
    request_id: str
    symbol: str
    order_type: str  # 'buy' or 'sell'
    volume: float
    price: float
    stop_loss: float
    take_profit: float
    comment: str
    timestamp: datetime
    max_retries: int = 3
    timeout_seconds: int = 30

@dataclass
class ExecutionResult:
    """Execution result information"""
    request_id: str
    status: ExecutionStatus
    order_ticket: Optional[int]
    executed_price: Optional[float]
    executed_volume: Optional[float]
    slippage: Optional[float]
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    safety_level: SafetyLevel
    timestamp: datetime

@dataclass
class SafetyCheck:
    """Safety check result"""
    is_safe: bool
    safety_level: SafetyLevel
    warnings: List[str]
    errors: List[str]
    recommendations: List[str]

class ExecutionSafetyLayer:
    """Safety layer around MT5 execution"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.execution_history = []
        self.pending_requests = {}
        self.is_monitoring = False
        
        # Safety thresholds (configurable)
        self.thresholds = {
            'max_slippage_pips': 5.0,          # Maximum allowed slippage
            'max_execution_time_ms': 1000,     # Maximum execution time
            'max_spread_multiplier': 3.0,      # Maximum spread vs average
            'min_account_margin_percent': 10.0, # Minimum margin requirement
            'max_retries': 3,                  # Maximum retry attempts
            'retry_delay_seconds': 1.0,        # Delay between retries
            'order_timeout_seconds': 30,        # Order timeout
            'price_deviation_threshold': 0.001, # 0.1% price deviation
            'volume_safety_margin': 0.1        # 10% volume safety margin
        }
        
        # Safety statistics
        self.safety_stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'retried_executions': 0,
            'cancelled_executions': 0,
            'average_slippage': 0.0,
            'average_execution_time': 0.0,
            'safety_violations': 0
        }
        
        # Recent market data for comparison
        self.recent_market_data = {}
        
    async def execute_order_safely(self, symbol: str, order_type: str, volume: float,
                                 price: float, stop_loss: float, take_profit: float,
                                 comment: str = "UOTA Elite v2") -> ExecutionResult:
        """Execute order with comprehensive safety checks"""
        try:
            # Generate unique request ID
            request_id = f"exec_{int(time.time() * 1000)}_{symbol}"
            
            # Create execution request
            request = ExecutionRequest(
                request_id=request_id,
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=comment,
                timestamp=datetime.now()
            )
            
            self.logger.info(f"🛡️ Safe execution request: {request_id} - {symbol} {volume} lots {order_type}")
            
            # Pre-execution safety checks
            safety_check = await self._pre_execution_safety_check(request)
            
            if not safety_check.is_safe:
                self.logger.error(f"🚨 SAFETY BLOCK: {request_id} - {'; '.join(safety_check.errors)}")
                return ExecutionResult(
                    request_id=request_id,
                    status=ExecutionStatus.CANCELLED,
                    order_ticket=None,
                    executed_price=None,
                    executed_volume=None,
                    slippage=None,
                    execution_time_ms=None,
                    error_message=f"Safety check failed: {'; '.join(safety_check.errors)}",
                    safety_level=safety_check.safety_level,
                    timestamp=datetime.now()
                )
            
            # Log safety warnings
            for warning in safety_check.warnings:
                self.logger.warning(f"⚠️ SAFETY WARNING: {request_id} - {warning}")
            
            # Execute with retry logic
            result = await self._execute_with_retry(request)
            
            # Post-execution validation
            if result.status == ExecutionStatus.SUCCESS:
                result = await self._post_execution_validation(request, result)
            
            # Update statistics
            await self._update_statistics(result)
            
            # Log result
            await self._log_execution_result(request, result, safety_check)
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Critical error in safe execution: {e}")
            return ExecutionResult(
                request_id=request_id if 'request_id' in locals() else "unknown",
                status=ExecutionStatus.FAILED,
                order_ticket=None,
                executed_price=None,
                executed_volume=None,
                slippage=None,
                execution_time_ms=None,
                error_message=f"Critical error: {e}",
                safety_level=SafetyLevel.CRITICAL,
                timestamp=datetime.now()
            )
    
    async def _pre_execution_safety_check(self, request: ExecutionRequest) -> SafetyCheck:
        """Comprehensive pre-execution safety checks"""
        try:
            is_safe = True
            safety_level = SafetyLevel.SAFE
            warnings = []
            errors = []
            recommendations = []
            
            # 1. Account safety check
            account_safety, account_issues = await self._check_account_safety(request)
            if not account_safety:
                is_safe = False
                errors.extend(account_issues)
                safety_level = SafetyLevel.CRITICAL
            
            # 2. Market conditions check
            market_safety, market_issues = await self._check_market_conditions(request)
            if not market_safety:
                is_safe = False
                errors.extend(market_issues)
                safety_level = SafetyLevel.RISKY
            
            # 3. Order parameters check
            order_safety, order_warnings = await self._check_order_parameters(request)
            warnings.extend(order_warnings)
            
            # 4. Connection stability check
            connection_safety, connection_issues = await self._check_connection_stability()
            if not connection_safety:
                is_safe = False
                errors.extend(connection_issues)
                safety_level = SafetyLevel.CRITICAL
            
            # 5. Price reasonableness check
            price_safety, price_warnings = await self._check_price_reasonableness(request)
            warnings.extend(price_warnings)
            
            # Determine overall safety level
            if errors:
                safety_level = SafetyLevel.CRITICAL
            elif len(warnings) > 2:
                safety_level = SafetyLevel.RISKY
            elif warnings:
                safety_level = SafetyLevel.WARNING
            
            # Generate recommendations
            recommendations = await self._generate_safety_recommendations(warnings, errors)
            
            return SafetyCheck(
                is_safe=is_safe,
                safety_level=safety_level,
                warnings=warnings,
                errors=errors,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error in pre-execution safety check: {e}")
            return SafetyCheck(
                is_safe=False,
                safety_level=SafetyLevel.CRITICAL,
                warnings=[],
                errors=[f"Safety check error: {e}"],
                recommendations=["Abort execution immediately"]
            )
    
    async def _check_account_safety(self, request: ExecutionRequest) -> Tuple[bool, List[str]]:
        """Check account safety conditions"""
        try:
            issues = []
            
            # Get account information
            from mt5_integration # # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            account_info = await mt5_integration.get_account_balance()
            
            if not account_info:
                issues.append("Unable to retrieve account information")
                return False, issues
            
            # Check margin requirements
            balance = account_info.get('equity', 0)
            margin = account_info.get('margin', 0)
            free_margin = account_info.get('free_margin', 0)
            
            if balance <= 0:
                issues.append("Zero or negative account balance")
                return False, issues
            
            # Check margin usage
            margin_usage_percent = (margin / balance * 100) if balance > 0 else 100
            if margin_usage_percent > (100 - self.thresholds['min_account_margin_percent']):
                issues.append(f"Insufficient margin: {margin_usage_percent:.1f}% used")
                return False, issues
            
            # Check if order fits within available margin
            # Simplified margin calculation
            required_margin = request.volume * 1000  # Rough estimate
            if required_margin > free_margin:
                issues.append(f"Insufficient margin for order: required ${required_margin:.2f}, available ${free_margin:.2f}")
                return False, issues
            
            return True, issues
            
        except Exception as e:
            self.logger.error(f"❌ Error checking account safety: {e}")
            return False, [f"Account safety check error: {e}"]
    
    async def _check_market_conditions(self, request: ExecutionRequest) -> Tuple[bool, List[str]]:
        """Check market conditions"""
        try:
            issues = []
            
            # Get current market data
            from mt5_integration # # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            market_data = await mt5_integration.get_market_data(request.symbol, count=10)
            
            if not market_data:
                issues.append("Unable to retrieve market data")
                return False, issues
            
            # Check for abnormal spreads
            latest_data = market_data[-1]
            current_spread = latest_data.get('spread', 0)
            
            # Calculate average spread
            avg_spread = sum(d.get('spread', 0) for d in market_data) / len(market_data)
            
            if current_spread > avg_spread * self.thresholds['max_spread_multiplier']:
                issues.append(f"Abnormal spread: {current_spread} (avg: {avg_spread:.1f})")
                return False, issues
            
            # Check for high volatility
            if len(market_data) >= 2:
                price_changes = []
                for i in range(1, len(market_data)):
                    prev_close = market_data[i-1].get('close', 0)
                    curr_close = market_data[i].get('close', 0)
                    if prev_close > 0:
                        price_changes.append(abs((curr_close - prev_close) / prev_close))
                
                if price_changes:
                    avg_volatility = sum(price_changes) / len(price_changes)
                    if avg_volatility > 0.01:  # 1% average volatility
                        issues.append(f"High volatility detected: {avg_volatility*100:.2f}%")
                        return False, issues
            
            return True, issues
            
        except Exception as e:
            self.logger.error(f"❌ Error checking market conditions: {e}")
            return False, [f"Market conditions check error: {e}"]
    
    async def _check_order_parameters(self, request: ExecutionRequest) -> Tuple[bool, List[str]]:
        """Check order parameters"""
        try:
            warnings = []
            
            # Check volume
            if request.volume <= 0:
                warnings.append("Zero or negative volume")
            elif request.volume > 10.0:
                warnings.append(f"Large volume: {request.volume} lots")
            
            # Check price levels
            if request.stop_loss <= 0 or request.take_profit <= 0:
                warnings.append("Invalid stop loss or take profit")
            
            # Check stop loss distance
            if request.stop_loss > 0 and request.price > 0:
                stop_distance = abs(request.price - request.stop_loss) / request.price
                if stop_distance > 0.05:  # 5% stop distance
                    warnings.append(f"Wide stop loss: {stop_distance*100:.1f}%")
                elif stop_distance < 0.001:  # 0.1% stop distance
                    warnings.append(f"Tight stop loss: {stop_distance*100:.2f}%")
            
            # Check take profit distance
            if request.take_profit > 0 and request.price > 0:
                profit_distance = abs(request.take_profit - request.price) / request.price
                if profit_distance < 0.001:  # 0.1% profit distance
                    warnings.append(f"Tight take profit: {profit_distance*100:.2f}%")
            
            # Check risk:reward ratio
            if request.stop_loss > 0 and request.take_profit > 0 and request.price > 0:
                risk = abs(request.price - request.stop_loss)
                reward = abs(request.take_profit - request.price)
                if reward > 0:
                    rr_ratio = reward / risk
                    if rr_ratio < 0.5:  # Less than 1:2
                        warnings.append(f"Poor risk:reward ratio: 1:{rr_ratio:.1f}")
            
            return True, warnings
            
        except Exception as e:
            self.logger.error(f"❌ Error checking order parameters: {e}")
            return False, [f"Order parameters check error: {e}"]
    
    async def _check_connection_stability(self) -> Tuple[bool, List[str]]:
        """Check MT5 connection stability"""
        try:
            issues = []
            
            # Check MT5 connection
            from mt5_integration # # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            if not mt5_integration.is_connected:
                issues.append("MT5 not connected")
                return False, issues
            
            # Test connection with a quick account check
            try:
                account_info = await mt5_integration.get_account_balance()
                if not account_info:
                    issues.append("MT5 connection test failed")
                    return False, issues
            except Exception as e:
                issues.append(f"MT5 connection error: {e}")
                return False, issues
            
            return True, issues
            
        except Exception as e:
            self.logger.error(f"❌ Error checking connection stability: {e}")
            return False, [f"Connection stability check error: {e}"]
    
    async def _check_price_reasonableness(self, request: ExecutionRequest) -> Tuple[bool, List[str]]:
        """Check if requested price is reasonable"""
        try:
            warnings = []
            
            # Get current market data
            from mt5_integration # # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            market_data = await mt5_integration.get_market_data(request.symbol, count=5)
            
            if not market_data:
                warnings.append("Cannot validate price - no market data")
                return True, warnings
            
            # Get current price
            latest_data = market_data[-1]
            current_price = latest_data.get('close', 0)
            
            if current_price <= 0:
                warnings.append("Invalid current price")
                return True, warnings
            
            # Check price deviation
            price_deviation = abs(request.price - current_price) / current_price
            if price_deviation > self.thresholds['price_deviation_threshold']:
                warnings.append(f"Large price deviation: {price_deviation*100:.2f}% from market")
            
            # Check if price is within recent range
            recent_prices = [d.get('high', 0) for d in market_data] + [d.get('low', 0) for d in market_data]
            if recent_prices:
                min_price = min(recent_prices)
                max_price = max(recent_prices)
                
                if request.price < min_price * 0.95 or request.price > max_price * 1.05:
                    warnings.append(f"Price outside recent range: {min_price:.5f} - {max_price:.5f}")
            
            return True, warnings
            
        except Exception as e:
            self.logger.error(f"❌ Error checking price reasonableness: {e}")
            return False, [f"Price reasonableness check error: {e}"]
    
    async def _generate_safety_recommendations(self, warnings: List[str], errors: List[str]) -> List[str]:
        """Generate safety recommendations"""
        try:
            recommendations = []
            
            if errors:
                recommendations.append("Abort execution - critical safety issues detected")
            
            if "High volatility" in str(warnings):
                recommendations.append("Consider waiting for market to stabilize")
            
            if "Abnormal spread" in str(warnings):
                recommendations.append("Consider waiting for spread normalization")
            
            if "Large volume" in str(warnings):
                recommendations.append("Consider reducing position size")
            
            if "Wide stop loss" in str(warnings):
                recommendations.append("Consider tightening stop loss")
            
            if "Poor risk:reward" in str(warnings):
                recommendations.append("Consider adjusting take profit level")
            
            if not recommendations and warnings:
                recommendations.append("Proceed with caution - monitor execution closely")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"❌ Error generating safety recommendations: {e}")
            return ["Error generating recommendations"]
    
    async def _execute_with_retry(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute order with retry logic"""
        try:
            start_time = time.time()
            last_error = None
            
            for attempt in range(request.max_retries + 1):
                try:
                    # Execute order
                    from mt5_integration # # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                    order_ticket = await mt5_integration.place_order(
                        symbol=request.symbol,
                        order_type=request.order_type,
                        volume=request.volume,
                        price=request.price,
                        stop_loss=request.stop_loss,
                        take_profit=request.take_profit,
                        comment=request.comment
                    )
                    
                    if order_ticket:
                        execution_time = int((time.time() - start_time) * 1000)
                        
                        return ExecutionResult(
                            request_id=request.request_id,
                            status=ExecutionStatus.SUCCESS,
                            order_ticket=order_ticket,
                            executed_price=request.price,
                            executed_volume=request.volume,
                            slippage=0.0,  # Will be calculated in post-validation
                            execution_time_ms=execution_time,
                            error_message=None,
                            safety_level=SafetyLevel.SAFE,
                            timestamp=datetime.now()
                        )
                    else:
                        last_error = "Order placement returned None"
                        
                except Exception as e:
                    last_error = str(e)
                    self.logger.warning(f"⚠️ Execution attempt {attempt + 1} failed: {e}")
                
                # If not last attempt, wait before retry
                if attempt < request.max_retries:
                    await asyncio.sleep(self.thresholds['retry_delay_seconds'])
            
            # All attempts failed
            execution_time = int((time.time() - start_time) * 1000)
            
            return ExecutionResult(
                request_id=request.request_id,
                status=ExecutionStatus.FAILED,
                order_ticket=None,
                executed_price=None,
                executed_volume=None,
                slippage=None,
                execution_time_ms=execution_time,
                error_message=f"All retries failed: {last_error}",
                safety_level=SafetyLevel.CRITICAL,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"❌ Critical error in execution with retry: {e}")
            return ExecutionResult(
                request_id=request.request_id,
                status=ExecutionStatus.FAILED,
                order_ticket=None,
                executed_price=None,
                executed_volume=None,
                slippage=None,
                execution_time_ms=None,
                error_message=f"Critical execution error: {e}",
                safety_level=SafetyLevel.CRITICAL,
                timestamp=datetime.now()
            )
    
    async def _post_execution_validation(self, request: ExecutionRequest, 
                                      result: ExecutionResult) -> ExecutionResult:
        """Validate execution result"""
        try:
            # Get current market data to calculate slippage
            from mt5_integration # # # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            current_data = await mt5_integration.get_market_data(request.symbol, count=1)
            
            if current_data:
                current_price = current_data[-1].get('close', 0)
                if current_price > 0 and result.executed_price:
                    slippage_pips = abs(current_price - result.executed_price) / current_price * 10000
                    result.slippage = slippage_pips
                    
                    # Check for excessive slippage
                    if slippage_pips > self.thresholds['max_slippage_pips']:
                        self.logger.warning(f"⚠️ High slippage detected: {slippage_pips:.1f} pips")
                        result.safety_level = SafetyLevel.WARNING
            
            # Verify order was actually placed
            if result.order_ticket:
                try:
                    positions = await mt5_integration.get_positions()
                    order_exists = any(pos.ticket == result.order_ticket for pos in positions)
                    
                    if not order_exists:
                        self.logger.warning(f"⚠️ Order ticket {result.order_ticket} not found in positions")
                        result.status = ExecutionStatus.FAILED
                        result.error_message = "Order not found in positions"
                        result.safety_level = SafetyLevel.CRITICAL
                        
                except Exception as e:
                    self.logger.error(f"❌ Error verifying order: {e}")
                    result.safety_level = SafetyLevel.WARNING
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Error in post-execution validation: {e}")
            result.safety_level = SafetyLevel.WARNING
            return result
    
    async def _update_statistics(self, result: ExecutionResult):
        """Update execution statistics"""
        try:
            self.safety_stats['total_executions'] += 1
            
            if result.status == ExecutionStatus.SUCCESS:
                self.safety_stats['successful_executions'] += 1
            elif result.status == ExecutionStatus.FAILED:
                self.safety_stats['failed_executions'] += 1
            elif result.status == ExecutionStatus.CANCELLED:
                self.safety_stats['cancelled_executions'] += 1
            
            # Update slippage statistics
            if result.slippage is not None:
                current_avg = self.safety_stats['average_slippage']
                total_count = self.safety_stats['successful_executions']
                self.safety_stats['average_slippage'] = (current_avg * (total_count - 1) + result.slippage) / total_count
            
            # Update execution time statistics
            if result.execution_time_ms is not None:
                current_avg = self.safety_stats['average_execution_time']
                total_count = self.safety_stats['total_executions']
                self.safety_stats['average_execution_time'] = (current_avg * (total_count - 1) + result.execution_time_ms) / total_count
            
            # Update safety violations
            if result.safety_level in [SafetyLevel.RISKY, SafetyLevel.CRITICAL]:
                self.safety_stats['safety_violations'] += 1
                
        except Exception as e:
            self.logger.error(f"❌ Error updating statistics: {e}")
    
    async def _log_execution_result(self, request: ExecutionRequest, 
                                   result: ExecutionResult, safety_check: SafetyCheck):
        """Log execution result"""
        try:
            # Add to history
            self.execution_history.append((request, result, safety_check))
            
            # Keep only last 1000 executions
            if len(self.execution_history) > 1000:
                self.execution_history = self.execution_history[-1000:]
            
            # Log to file
            log_entry = {
                'timestamp': result.timestamp.isoformat(),
                'request_id': result.request_id,
                'symbol': request.symbol,
                'order_type': request.order_type,
                'volume': request.volume,
                'requested_price': request.price,
                'status': result.status.value,
                'order_ticket': result.order_ticket,
                'executed_price': result.executed_price,
                'slippage': result.slippage,
                'execution_time_ms': result.execution_time_ms,
                'safety_level': result.safety_level.value,
                'safety_warnings': safety_check.warnings,
                'safety_errors': safety_check.errors,
                'error_message': result.error_message
            }
            
            os.makedirs('logs/execution', exist_ok=True)
            log_file = f"logs/execution/execution_safety_{datetime.now().strftime('%Y-%m-%d')}.json"
            
            # Read existing logs
            existing_logs = []
            if os.path.exists(log_file):
                async with aiofiles.open(log_file, 'r') as f:
                    content = await f.read()
                    if content:
                        existing_logs = json.loads(content)
            
            # Add new log
            existing_logs.append(log_entry)
            
            # Keep only last 24 hours
            cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
            existing_logs = [log for log in existing_logs if log['timestamp'] > cutoff_time]
            
            # Save logs
            async with aiofiles.open(log_file, 'w') as f:
                await f.write(json.dumps(existing_logs, indent=2))
            
            # Log to console
            if result.status == ExecutionStatus.SUCCESS:
                self.logger.info(f"✅ Safe execution successful: {result.request_id} - Ticket: {result.order_ticket}")
            elif result.status == ExecutionStatus.CANCELLED:
                self.logger.warning(f"⚠️ Execution cancelled: {result.request_id} - {result.error_message}")
            else:
                self.logger.error(f"❌ Execution failed: {result.request_id} - {result.error_message}")
                
        except Exception as e:
            self.logger.error(f"❌ Error logging execution result: {e}")
    
    def get_safety_summary(self) -> Dict[str, Any]:
        """Get safety summary for dashboard"""
        try:
            # Calculate success rate
            total = self.safety_stats['total_executions']
            success_rate = (self.safety_stats['successful_executions'] / total * 100) if total > 0 else 0
            
            # Calculate safety violation rate
            violation_rate = (self.safety_stats['safety_violations'] / total * 100) if total > 0 else 0
            
            return {
                'total_executions': total,
                'successful_executions': self.safety_stats['successful_executions'],
                'failed_executions': self.safety_stats['failed_executions'],
                'cancelled_executions': self.safety_stats['cancelled_executions'],
                'success_rate': success_rate,
                'average_slippage_pips': self.safety_stats['average_slippage'],
                'average_execution_time_ms': self.safety_stats['average_execution_time'],
                'safety_violations': self.safety_stats['safety_violations'],
                'safety_violation_rate': violation_rate,
                'thresholds': self.thresholds,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting safety summary: {e}")
            return {'error': str(e)}

# Global execution safety layer instance
execution_safety_layer = ExecutionSafetyLayer()
