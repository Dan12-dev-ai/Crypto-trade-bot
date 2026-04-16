#!/usr/bin/env python3
"""
UOTA Elite v2 - Defensive Error Handler
The Shield: Comprehensive error handling with back-off logic
"""

import asyncio
import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class BackoffConfig:
    """Backoff configuration for retries"""
    initial_delay: float = 5.0  # seconds
    max_delay: float = 300.0  # 5 minutes
    backoff_multiplier: float = 2.0
    max_retries: int = 5
    jitter: bool = True

@dataclass
class InputValidation:
    """Input validation rules"""
    min_lot_size: float = 0.01
    max_lot_size: float = 10.0
    min_stop_loss: float = 1.0
    max_stop_loss: float = 1000.0
    min_take_profit: float = 1.0
    max_take_profit: float = 1000.0
    allowed_symbols: List[str] = None

class DefensiveErrorHandler:
    """Defensive error handling system"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.backoff_config = BackoffConfig()
        self.input_validation = InputValidation()
        self.error_history = []
        self.connection_errors = 0
        self.last_connection_error = None
        
    def _setup_logging(self):
        """Setup comprehensive logging"""
        os.makedirs('logs', exist_ok=True)
        
        # Create separate loggers
        self.info_logger = self._create_logger('info', 'logs/info.log')
        self.error_logger = self._create_logger('error', 'logs/error.log')
        self.debug_logger = self._create_logger('debug', 'logs/debug.log')
        
        return self.info_logger
    
    def _create_logger(self, name: str, filename: str):
        """Create logger with specific configuration"""
        logger = logging.getLogger(f'uota_{name}')
        logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    async def safe_mt5_operation(self, operation_name: str, operation_func, *args, **kwargs) -> Any:
        """Execute MT5 operation with comprehensive error handling"""
        attempt = 0
        last_error = None
        
        while attempt < self.backoff_config.max_retries:
            try:
                self.debug_logger.debug(f"🔄 {operation_name} - Attempt {attempt + 1}/{self.backoff_config.max_retries}")
                
                # Execute operation with timeout
                result = await asyncio.wait_for(
                    operation_func(*args, **kwargs),
                    timeout=30.0
                )
                
                # Log successful operation
                self.info_logger.info(f"✅ {operation_name} - Success (Attempt {attempt + 1})")
                
                # Reset connection error counter on success
                self.connection_errors = 0
                self.last_connection_error = None
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after 30s (Attempt {attempt + 1})"
                self.error_logger.error(f"⏰ {operation_name} - {last_error}")
                
            except ConnectionError as e:
                last_error = f"ConnectionError: {str(e)} (Attempt {attempt + 1})"
                self.error_logger.error(f"🔌 {operation_name} - {last_error}")
                
                # Track connection errors for backoff
                self.connection_errors += 1
                self.last_connection_error = datetime.now()
                
                # Implement backoff logic
                if self.connection_errors >= 3:
                    delay = self._calculate_backoff_delay(attempt)
                    self.error_logger.warning(f"⏳ Backoff: Waiting {delay:.1f}s before retry")
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(self.backoff_config.initial_delay)
                
            except Exception as e:
                last_error = f"Exception: {str(e)} (Attempt {attempt + 1})"
                self.error_logger.error(f"❌ {operation_name} - {last_error}")
                
                # Check if error is retryable
                if self._is_retryable_error(str(e)):
                    delay = self._calculate_backoff_delay(attempt)
                    self.error_logger.warning(f"⏳ Retryable error: Waiting {delay:.1f}s before retry")
                    await asyncio.sleep(delay)
                else:
                    self.error_logger.error(f"🚨 Non-retryable error: {str(e)}")
                    break
            
            attempt += 1
        
        # All retries failed
        final_error = f"{operation_name} failed after {attempt} attempts: {last_error}"
        self.error_logger.critical(f"🚨 {final_error}")
        
        # Alert user if connection errors persist
        if self.connection_errors >= 3:
            await self._send_connection_alert(operation_name, attempt, last_error)
        
        raise Exception(final_error)
    
    def _calculate_backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay with jitter"""
        delay = min(
            self.backoff_config.initial_delay * (self.backoff_config.backoff_multiplier ** attempt),
            self.backoff_config.max_delay
        )
        
        # Add jitter to prevent thundering herd
        if self.backoff_config.jitter:
            import random
            jitter = random.uniform(0.8, 1.2)
            delay *= jitter
        
        return delay
    
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
            'dns error',
            'connection reset',
            'connection aborted'
        ]
        
        error_lower = error_message.lower()
        return any(retryable_error in error_lower for retryable_error in retryable_errors)
    
    async def _send_connection_alert(self, operation_name: str, attempts: int, last_error: str):
        """Send connection alert to user"""
        try:
            from cloud_telegram_c2 import cloud_telegram_c2
            
            alert_message = f"""
🚨 **CONNECTION ALERT**
═══════════════════════════════════
Operation: {operation_name}
Attempts: {attempts}
Connection Errors: {self.connection_errors}
Last Error: {last_error}
Time: {datetime.now().strftime('%H:%M:%S')}
Status: 🔌 PERSISTENT CONNECTION ISSUES

📍 Location: Bahir Dar Network
🌐 Issue: Internet connectivity problems
⏱️ Duration: {(datetime.now() - self.last_connection_error).total_seconds():.1f}s
🔧 Action: Check internet connection
"""
            
            await cloud_telegram_c2.send_message(alert_message)
            
        except Exception as e:
            self.error_logger.error(f"❌ Failed to send connection alert: {e}")
    
    def sanitize_trade_input(self, trade_data: Dict) -> Dict:
        """Sanitize and validate trade input"""
        try:
            self.debug_logger.debug(f"🔍 Sanitizing trade input: {trade_data}")
            
            sanitized = trade_data.copy()
            
            # Validate lot size
            lot_size = float(trade_data.get('lot_size', 0))
            if lot_size is None or lot_size <= 0:
                lot_size = self.input_validation.min_lot_size
                self.error_logger.warning(f"⚠️ Invalid lot size, using default: {lot_size}")
            
            sanitized['lot_size'] = max(self.input_validation.min_lot_size, 
                                      min(lot_size, self.input_validation.max_lot_size))
            
            # Validate stop loss
            stop_loss = float(trade_data.get('stop_loss', 0))
            if stop_loss is None or stop_loss <= 0:
                stop_loss = self.input_validation.min_stop_loss
                self.error_logger.warning(f"⚠️ Invalid stop loss, using default: {stop_loss}")
            
            sanitized['stop_loss'] = max(self.input_validation.min_stop_loss,
                                      min(stop_loss, self.input_validation.max_stop_loss))
            
            # Validate take profit
            take_profit = float(trade_data.get('take_profit', 0))
            if take_profit is None or take_profit <= 0:
                take_profit = self.input_validation.min_take_profit
                self.error_logger.warning(f"⚠️ Invalid take profit, using default: {take_profit}")
            
            sanitized['take_profit'] = max(self.input_validation.min_take_profit,
                                        min(take_profit, self.input_validation.max_take_profit))
            
            # Validate symbol
            symbol = trade_data.get('symbol', '').upper()
            if self.input_validation.allowed_symbols and symbol not in self.input_validation.allowed_symbols:
                symbol = 'XAUUSD'  # Default to gold
                self.error_logger.warning(f"⚠️ Invalid symbol, using default: {symbol}")
            
            sanitized['symbol'] = symbol
            
            # Add validation timestamp
            sanitized['sanitized_at'] = datetime.now().isoformat()
            sanitized['validation_passed'] = True
            
            self.info_logger.info(f"✅ Trade input sanitized: {symbol} {sanitized['lot_size']} lots")
            
            return sanitized
            
        except Exception as e:
            self.error_logger.error(f"❌ Error sanitizing trade input: {e}")
            return {
                'validation_passed': False,
                'error': str(e),
                'sanitized_at': datetime.now().isoformat()
            }
    
    def validate_price_data(self, price_data: Any) -> Dict:
        """Validate price data"""
        try:
            self.debug_logger.debug(f"🔍 Validating price data: {price_data}")
            
            validation_result = {
                'valid': False,
                'price': None,
                'timestamp': None,
                'symbol': None,
                'errors': []
            }
            
            if price_data is None:
                validation_result['errors'].append("Price data is None")
                return validation_result
            
            # Check for required fields
            if hasattr(price_data, 'bid'):
                if price_data.bid is None or price_data.bid <= 0:
                    validation_result['errors'].append("Invalid bid price")
                else:
                    validation_result['bid'] = float(price_data.bid)
            
            if hasattr(price_data, 'ask'):
                if price_data.ask is None or price_data.ask <= 0:
                    validation_result['errors'].append("Invalid ask price")
                else:
                    validation_result['ask'] = float(price_data.ask)
            
            if hasattr(price_data, 'symbol'):
                if price_data.symbol is None or not price_data.symbol:
                    validation_result['errors'].append("Invalid symbol")
                else:
                    validation_result['symbol'] = str(price_data.symbol)
            
            # Add timestamp
            validation_result['timestamp'] = datetime.now().isoformat()
            validation_result['valid'] = len(validation_result['errors']) == 0
            
            if validation_result['valid']:
                self.info_logger.info(f"✅ Price data validated: {validation_result.get('symbol', 'Unknown')}")
            else:
                self.error_logger.error(f"❌ Price data validation failed: {validation_result['errors']}")
            
            return validation_result
            
        except Exception as e:
            self.error_logger.error(f"❌ Error validating price data: {e}")
            return {
                'valid': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def log_trade_execution(self, trade_data: Dict, result: Dict):
        """Log trade execution with comprehensive details"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'trade_id': trade_data.get('trade_id', ''),
                'symbol': trade_data.get('symbol', ''),
                'type': trade_data.get('type', ''),
                'lot_size': trade_data.get('lot_size', 0),
                'entry_price': trade_data.get('entry_price', 0),
                'stop_loss': trade_data.get('stop_loss', 0),
                'take_profit': trade_data.get('take_profit', 0),
                'result': result,
                'execution_time': result.get('execution_time', 0),
                'commission': result.get('commission', 0),
                'swap': result.get('swap', 0),
                'profit': result.get('profit', 0),
                'reason': result.get('reason', ''),
                'success': result.get('success', False)
            }
            
            # Log to appropriate level
            if result.get('success', False):
                self.info_logger.info(f"📈 TRADE EXECUTED: {log_entry['symbol']} {log_entry['type']} {log_entry['lot_size']} lots @ {log_entry['entry_price']}")
            else:
                self.error_logger.error(f"❌ TRADE FAILED: {log_entry['symbol']} - {log_entry['reason']}")
            
            # Log detailed debug info
            self.debug_logger.debug(f"🔍 TRADE DEBUG: {json.dumps(log_entry, indent=2)}")
            
            # Store in error history
            self.error_history.append(log_entry)
            
            # Keep history manageable
            if len(self.error_history) > 1000:
                self.error_history = self.error_history[-500:]
            
        except Exception as e:
            self.error_logger.error(f"❌ Error logging trade execution: {e}")
    
    def get_error_statistics(self) -> Dict:
        """Get error statistics"""
        try:
            if not self.error_history:
                return {'message': 'No error history available'}
            
            # Calculate statistics
            total_errors = len(self.error_history)
            successful_trades = len([e for e in self.error_history if e.get('success', False)])
            failed_trades = len([e for e in self.error_history if not e.get('success', False)])
            
            # Recent errors (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_errors = len([e for e in self.error_history 
                              if datetime.fromisoformat(e['timestamp']) > cutoff_time])
            
            # Connection errors
            connection_errors = len([e for e in self.error_history 
                                   if 'connection' in e.get('reason', '').lower()])
            
            return {
                'total_errors': total_errors,
                'successful_trades': successful_trades,
                'failed_trades': failed_trades,
                'success_rate': (successful_trades / total_errors * 100) if total_errors > 0 else 0,
                'recent_errors_24h': recent_errors,
                'connection_errors': connection_errors,
                'current_connection_errors': self.connection_errors,
                'last_connection_error': self.last_connection_error.isoformat() if self.last_connection_error else None,
                'error_rate': (recent_errors / total_errors * 100) if total_errors > 0 else 0
            }
            
        except Exception as e:
            self.error_logger.error(f"❌ Error calculating statistics: {e}")
            return {'error': str(e)}
    
    def reset_error_counters(self):
        """Reset error counters"""
        self.connection_errors = 0
        self.last_connection_error = None
        self.info_logger.info("🔄 Error counters reset")

# Global defensive error handler
defensive_error_handler = DefensiveErrorHandler()
