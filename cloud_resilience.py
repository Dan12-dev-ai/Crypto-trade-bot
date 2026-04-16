#!/usr/bin/env python3
"""
UOTA Elite v2 - Cloud Resilience System
Error-free operation with rotating logs and MT5 retry logic
"""

# import asyncio
# import logging
# import json
# import os
# import time
from datetime import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
# import threading

@dataclass
class RetryConfig:
    """Retry configuration for MT5 operations"""
    max_retries: int = 3
    retry_delay: float = 5.0  # seconds
    backoff_multiplier: float = 2.0
    timeout: float = 30.0  # seconds

class CloudResilience:
    """Cloud resilience system for error-free operation"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.retry_config = RetryConfig()
        self.connection_status = False
        self.last_connection_time = None
        self.retry_count = 0
        self.max_retry_count = 100
        
        # Rotating logs
        self.log_rotation_days = 7
        self.log_files = {
            'trades': 'logs/trades.json',
            'errors': 'logs/errors.json',
            'connections': 'logs/connections.json',
            'performance': 'logs/performance.json'
        }
        
        # Thread safety
        self.log_lock = threading.Lock()
        
    def _setup_logging(self):
        """Setup logging with rotation"""
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Setup file logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/cloud_resilience.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    async def safe_mt5_operation(self, operation_name: str, operation_func, *args, **kwargs) -> Any:
        """Execute MT5 operation with comprehensive error handling"""
        for attempt in range(self.retry_config.max_retries):
            try:
                self.logger.debug(f" {operation_name} - Attempt {attempt + 1}/{self.retry_config.max_retries}")
                
                # Execute operation with timeout
                result = await asyncio.wait_for(
                    operation_func(*args, **kwargs),
                    timeout=self.retry_config.timeout
                )
                
                # Log successful operation
                await self._log_operation(operation_name, 'SUCCESS', attempt + 1, result)
                
                # Reset retry count on success
                self.retry_count = 0
                
                return result
                
            except asyncio.TimeoutError:
                error_msg = f"Timeout after {self.retry_config.timeout}s"
                self.logger.warning(f" {operation_name} - {error_msg} (Attempt {attempt + 1})")
                await self._log_operation(operation_name, 'TIMEOUT', attempt + 1, error_msg)
                
            except Exception as e:
                error_msg = str(e)
                self.logger.warning(f" {operation_name} - {error_msg} (Attempt {attempt + 1})")
                await self._log_operation(operation_name, 'ERROR', attempt + 1, error_msg)
                
                # Check if error is retryable
                if not self._is_retryable_error(error_msg):
                    self.logger.error(f" {operation_name} - Non-retryable error: {error_msg}")
                    raise e
            
            # Wait before retry
            if attempt < self.retry_config.max_retries - 1:
                delay = self.retry_config.retry_delay * (self.retry_config.backoff_multiplier ** attempt)
                self.logger.info(f" Retrying {operation_name} in {delay:.1f}s...")
                await asyncio.sleep(delay)
        
        # All retries failed
        final_error = f"{operation_name} failed after {self.retry_config.max_retries} attempts"
        self.logger.error(f" {final_error}")
        await self._log_operation(operation_name, 'FAILED', self.retry_config.max_retries, final_error)
        
        raise Exception(final_error)
    
    def _is_retryable_error(self, error_message: str) -> bool:
        """Check if error is retryable"""
        retryable_errors = [
            'connection lost',
            'timeout',
            'network error',
            'server busy',
            'off-quotes',
            'requote',
            'invalid request',
            'connection refused',
            'temporary failure',
            'service unavailable',
            'rate limit',
            'socket error',
            'dns error'
        ]
        
        error_lower = error_message.lower()
        return any(retryable_error in error_lower for retryable_error in retryable_errors)
    
    async def _log_operation(self, operation: str, status: str, attempt: int, details: Any):
        """Log operation with rotation"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'status': status,
                'attempt': attempt,
                'details': str(details) if details else '',
                'retry_count': self.retry_count
            }
            
            # Determine log file
            if status in ['SUCCESS']:
                log_file = self.log_files['performance']
            elif status in ['ERROR', 'FAILED', 'TIMEOUT']:
                log_file = self.log_files['errors']
            else:
                log_file = self.log_files['connections']
            
            # Thread-safe logging
            with self.log_lock:
                await self._write_to_rotating_log(log_file, log_entry)
                
        except Exception as e:
            self.logger.error(f" Error logging operation: {e}")
    
    async def _write_to_rotating_log(self, log_file: str, log_entry: Dict):
        """Write to rotating log file"""
        try:
            # Read existing logs
            logs = []
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    try:
                        logs = json.load(f)
                    except json.JSONDecodeError:
                        logs = []
            
            # Add new entry
            logs.append(log_entry)
            
            # Rotate logs (keep only last 7 days)
            cutoff_date = datetime.now() - timedelta(days=self.log_rotation_days)
            logs = [log for log in logs if 
                     datetime.fromisoformat(log['timestamp']) > cutoff_date]
            
            # Write back to file
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2, default=str)
            
            # Keep file size manageable (max 1000 entries)
            if len(logs) > 1000:
                logs = logs[-1000:]
                with open(log_file, 'w') as f:
                    json.dump(logs, f, indent=2, default=str)
            
        except Exception as e:
            self.logger.error(f" Error writing to rotating log: {e}")
    
    async def monitor_connection_health(self):
        """Monitor connection health and auto-reconnect"""
        try:
            while self.is_running:
                try:
                    # Test connection
                    connection_status = await self._test_mt5_connection()
                    
                    if connection_status != self.connection_status:
                        # Connection status changed
                        self.connection_status = connection_status
                        self.last_connection_time = datetime.now()
                        
                        await self._log_operation(
                            'CONNECTION_STATUS_CHANGE',
                            'INFO' if connection_status else 'ERROR',
                            1,
                            f"Connection {'ESTABLISHED' if connection_status else 'LOST'}"
                        )
                        
                        # Send notification
                        await self._send_connection_notification(connection_status)
                    
                    # If connection is lost, attempt reconnection
                    if not connection_status:
                        self.retry_count += 1
                        
                        if self.retry_count <= self.max_retry_count:
                            self.logger.info(f" Attempting reconnection #{self.retry_count}")
                            
                            # Wait before reconnection attempt
                            await asyncio.sleep(self.retry_config.retry_delay)
                            
                            # Try to reconnect
                            reconnected = await self._attempt_reconnection()
                            
                            if reconnected:
                                self.retry_count = 0
                                self.connection_status = True
                                self.last_connection_time = datetime.now()
                                
                                await self._log_operation(
                                    'RECONNECTION',
                                    'SUCCESS',
                                    self.retry_count,
                                    f"Reconnected after {self.retry_count} attempts"
                                )
                            else:
                                await self._log_operation(
                                    'RECONNECTION',
                                    'FAILED',
                                    self.retry_count,
                                    f"Reconnection attempt {self.retry_count} failed"
                                )
                        else:
                            self.logger.error(f" Max retry count ({self.max_retry_count}) reached")
                            break
                    
                    # Wait before next check
                    await asyncio.sleep(10)  # Check every 10 seconds
                    
                except Exception as e:
                    self.logger.error(f" Error in connection monitoring: {e}")
                    await asyncio.sleep(10)
                    
        except asyncio.CancelledError:
            self.logger.info(" Connection monitoring stopped")
        except Exception as e:
            self.logger.error(f" Fatal error in connection monitoring: {e}")
    
    async def _test_mt5_connection(self) -> bool:
        """Test MT5 connection"""
        try:
            from mt5_integration # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            # Quick connection test
            connected = await mt5_integration.initialize()
            
            if connected:
                # Test basic operation
                account_info = await mt5_integration.get_account_balance()
                return account_info is not None
            else:
                return False
                
        except Exception as e:
            self.logger.error(f" Error testing MT5 connection: {e}")
            return False
    
    async def _attempt_reconnection(self) -> bool:
        """Attempt to reconnect to MT5"""
        try:
            from mt5_integration # # import mt5_integration  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            # Force reconnection
            await mt5_integration.shutdown()
            await asyncio.sleep(2)  # Wait before reconnect
            
            # Reconnect
            connected = await mt5_integration.initialize()
            
            if connected:
                self.logger.info(" MT5 reconnection successful")
                return True
            else:
                self.logger.warning(" MT5 reconnection failed")
                return False
                
        except Exception as e:
            self.logger.error(f" Error attempting reconnection: {e}")
            return False
    
    async def _send_connection_notification(self, status: bool):
        """Send connection status notification"""
        try:
            from cloud_telegram_c2 # import cloud_telegram_c2  # Moved to function to avoid circular import
            
            status_text = " ESTABLISHED" if status else " LOST"
            message = f"""
 **CONNECTION STATUS CHANGE**

MT5 Connection: {status_text}
Time: {datetime.now().strftime('%H:%M:%S')}
Retry Count: {self.retry_count}
Status: {' CONNECTED' if status else ' DISCONNECTED'}
"""
            
            await cloud_telegram_c2.send_message(message)
            
        except Exception as e:
            self.logger.error(f" Error sending connection notification: {e}")
    
    async def log_trade_execution(self, trade_data: Dict):
        """Log trade execution with rotation"""
        try:
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'symbol': trade_data.get('symbol', ''),
                'type': trade_data.get('type', ''),
                'volume': trade_data.get('volume', 0),
                'entry_price': trade_data.get('entry_price', 0),
                'exit_price': trade_data.get('exit_price', 0),
                'profit_loss': trade_data.get('profit_loss', 0),
                'commission': trade_data.get('commission', 0),
                'swap': trade_data.get('swap', 0),
                'order_id': trade_data.get('order_id', ''),
                'status': trade_data.get('status', ''),
                'reason': trade_data.get('reason', ''),
                'retry_count': trade_data.get('retry_count', 0)
            }
            
            # Write to trades log
            with self.log_lock:
                await self._write_to_rotating_log(self.log_files['trades'], trade_log)
                
        except Exception as e:
            self.logger.error(f" Error logging trade execution: {e}")
    
    def get_resilience_status(self) -> Dict:
        """Get resilience system status"""
        try:
            # Get log file sizes
            log_sizes = {}
            for log_type, log_file in self.log_files.items():
                if os.path.exists(log_file):
                    log_sizes[log_type] = os.path.getsize(log_file)
                else:
                    log_sizes[log_type] = 0
            
            return {
                'connection_status': self.connection_status,
                'last_connection_time': self.last_connection_time.isoformat() if self.last_connection_time else None,
                'retry_count': self.retry_count,
                'max_retry_count': self.max_retry_count,
                'log_rotation_days': self.log_rotation_days,
                'log_file_sizes': log_sizes,
                'retry_config': {
                    'max_retries': self.retry_config.max_retries,
                    'retry_delay': self.retry_config.retry_delay,
                    'backoff_multiplier': self.retry_config.backoff_multiplier,
                    'timeout': self.retry_config.timeout
                }
            }
            
        except Exception as e:
            self.logger.error(f" Error getting resilience status: {e}")
            return {}
    
    def cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.log_rotation_days)
            
            for log_file in self.log_files.values():
                if os.path.exists(log_file):
                    # Read logs
                    with open(log_file, 'r') as f:
                        try:
                            logs = json.load(f)
                        except json.JSONDecodeError:
                            logs = []
                    
                    # Filter old logs
                    filtered_logs = [log for log in logs if 
                                 datetime.fromisoformat(log['timestamp']) > cutoff_date]
                    
                    # Write back filtered logs
                    with open(log_file, 'w') as f:
                        json.dump(filtered_logs, f, indent=2, default=str)
            
            self.logger.info(f" Cleaned up logs older than {self.log_rotation_days} days")
            
        except Exception as e:
            self.logger.error(f" Error cleaning up old logs: {e}")
    
    async def start_resilience_monitoring(self):
        """Start resilience monitoring system"""
        try:
            self.logger.info(" Starting cloud resilience monitoring...")
            
            # Clean up old logs
            self.cleanup_old_logs()
            
            # Start connection monitoring
            await self.monitor_connection_health()
            
        except Exception as e:
            self.logger.error(f" Error starting resilience monitoring: {e}")

# Global resilience instance
cloud_resilience = CloudResilience()
