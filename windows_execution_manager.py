"""
UOTA Elite v2 - Windows Execution Manager
Error-free execution with automatic retry logic
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from typing import Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class ExecutionResult:
    """Trade execution result"""
    success: bool
    order_id: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    execution_time: float = 0.0

class WindowsExecutionManager:
    """Windows-specific execution manager with error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds
        self.critical_errors = [
            'Off-Quotes',
            'Requote',
            'Invalid Request',
            'Timeout',
            'Connection Lost'
        ]
    
    async def execute_trade_with_retry(self, 
                                     symbol: str,
                                     order_type: str,
                                     volume: float,
                                     price: float = 0.0,
                                     stop_loss: float = 0.0,
                                     take_profit: float = 0.0,
                                     comment: str = "UOTA Elite v2") -> ExecutionResult:
        """Execute trade with comprehensive error handling and retry logic"""
        
        start_time = time.time()
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                self.logger.info(f"🎯 EXECUTION ATTEMPT {retry_count + 1}/{self.max_retries + 1}")
                
                # Import MT5 integration
                from mt5_integration # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                
                # Execute trade
                order_id = await mt5_integration.place_order(
                    symbol=symbol,
                    order_type=0 if order_type.lower() == 'buy' else 1,
                    volume=volume,
                    price=price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    comment=comment
                )
                
                if order_id:
                    execution_time = time.time() - start_time
                    
                    # Send Telegram notification
                    await self._send_trade_notification(
                        symbol=symbol,
                        order_type=order_type,
                        volume=volume,
                        order_id=order_id,
                        success=True,
                        retry_count=retry_count
                    )
                    
                    self.logger.info(f"✅ TRADE EXECUTED: {symbol} {order_type} {volume} lots (Order ID: {order_id})")
                    
                    return ExecutionResult(
                        success=True,
                        order_id=order_id,
                        retry_count=retry_count,
                        execution_time=execution_time
                    )
                else:
                    raise Exception("Order placement returned None")
                    
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                self.logger.warning(f"⚠️ EXECUTION ERROR (Attempt {retry_count}): {e}")
                
                # Check if error requires retry
                if self._should_retry_error(last_error) and retry_count <= self.max_retries:
                    self.logger.info(f"🔄 RETRYING IN {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    break
        
        # All retries failed
        execution_time = time.time() - start_time
        
        # Send failure notification
        await self._send_trade_notification(
            symbol=symbol,
            order_type=order_type,
            volume=volume,
            order_id=None,
            success=False,
            error_message=last_error,
            retry_count=retry_count
        )
        
        self.logger.error(f"❌ TRADE EXECUTION FAILED: {symbol} {order_type} after {retry_count} attempts")
        
        return ExecutionResult(
            success=False,
            error_message=last_error,
            retry_count=retry_count,
            execution_time=execution_time
        )
    
    def _should_retry_error(self, error_message: str) -> bool:
        """Check if error should trigger retry"""
        error_lower = error_message.lower()
        
        # Critical errors that should be retried
        for critical_error in self.critical_errors:
            if critical_error.lower() in error_lower:
                return True
        
        # Network-related errors
        network_errors = ['connection', 'timeout', 'network', 'unreachable']
        for net_error in network_errors:
            if net_error in error_lower:
                return True
        
        # Temporary server errors
        temp_errors = ['server', 'busy', 'overloaded']
        for temp_error in temp_errors:
            if temp_error in error_lower:
                return True
        
        # Don't retry on permanent errors
        permanent_errors = ['invalid', 'forbidden', 'unauthorized', 'insufficient']
        for perm_error in permanent_errors:
            if perm_error in error_lower:
                return False
        
        return False
    
    async def close_position_with_retry(self, ticket: int) -> ExecutionResult:
        """Close position with retry logic"""
        
        start_time = time.time()
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                self.logger.info(f"🔒 CLOSING POSITION ATTEMPT {retry_count + 1}/{self.max_retries + 1} (Ticket: {ticket})")
                
                from mt5_integration # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                
                success = await mt5_integration.close_position(ticket)
                
                if success:
                    execution_time = time.time() - start_time
                    
                    self.logger.info(f"✅ POSITION CLOSED: Ticket {ticket}")
                    
                    return ExecutionResult(
                        success=True,
                        order_id=ticket,
                        retry_count=retry_count,
                        execution_time=execution_time
                    )
                else:
                    raise Exception("Position closure returned False")
                    
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                self.logger.warning(f"⚠️ CLOSE ERROR (Attempt {retry_count}): {e}")
                
                if self._should_retry_error(last_error) and retry_count <= self.max_retries:
                    self.logger.info(f"🔄 RETRYING CLOSE IN {self.retry_delay} seconds...")
                    await asyncio.sleep(self.retry_delay)
                else:
                    break
        
        execution_time = time.time() - start_time
        
        self.logger.error(f"❌ POSITION CLOSE FAILED: Ticket {ticket} after {retry_count} attempts")
        
        return ExecutionResult(
            success=False,
            error_message=last_error,
            retry_count=retry_count,
            execution_time=execution_time
        )
    
    async def _send_trade_notification(self, 
                                     symbol: str,
                                     order_type: str,
                                     volume: float,
                                     order_id: Optional[int],
                                     success: bool,
                                     retry_count: int = 0,
                                     error_message: Optional[str] = None):
        """Send Telegram notification for trade execution"""
        try:
            from telegram_notifications import telegram_notifier
            
            if success:
                message = f"""
🎯 **TRADE EXECUTED**
═════════════════════════════════════
Symbol: {symbol}
Type: {order_type.upper()}
Volume: {volume} lots
Order ID: {order_id}
Retries: {retry_count}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: ✅ SUCCESS
"""
            else:
                message = f"""
❌ **TRADE FAILED**
═════════════════════════════════════
Symbol: {symbol}
Type: {order_type.upper()}
Volume: {volume} lots
Retries: {retry_count}
Error: {error_message}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: ❌ FAILED
"""
            
            await telegram_notifier.send_message(message)
            
        except Exception as e:
            # Don't let notification failure break trade execution
            self.logger.warning(f"⚠️ Failed to send Telegram notification: {e}")
    
    async def validate_execution_conditions(self, symbol: str) -> bool:
        """Validate conditions before execution"""
        try:
            # Check market conditions
            from mt5_integration # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            symbol_info = await mt5_integration.get_symbol_info(symbol)
            if not symbol_info:
                self.logger.error(f"❌ Cannot get symbol info for {symbol}")
                return False
            
            # Check if market is open
            if not symbol_info.is_visible:
                self.logger.warning(f"⚠️ Market {symbol} is not visible")
                return False
            
            # Check spread
            if symbol_info.spread > 50:  # High spread threshold
                self.logger.warning(f"⚠️ High spread for {symbol}: {symbol_info.spread}")
                return False
            
            # Check account balance
            account_info = await mt5_integration.get_account_balance()
            if account_info.get('balance', 0) < 100:  # Minimum balance
                self.logger.error(f"❌ Insufficient balance: ${account_info.get('balance', 0):.2f}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error validating execution conditions: {e}")
            return False
    
    async def get_market_data_safe(self, symbol: str, timeframe: int, count: int = 100):
        """Get market data with error handling"""
        try:
            from mt5_integration # # # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            data = await mt5_integration.get_market_data(symbol, timeframe, count)
            
            if not data:
                self.logger.warning(f"⚠️ No market data for {symbol}")
                return []
            
            if len(data) < count:
                self.logger.warning(f"⚠️ Insufficient market data for {symbol}: {len(data)}/{count}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"❌ Error getting market data: {e}")
            return []

# Global execution manager instance
windows_execution_manager = WindowsExecutionManager()
