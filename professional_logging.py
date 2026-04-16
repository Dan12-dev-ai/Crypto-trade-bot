#!/usr/bin/env python3
"""
UOTA Elite v2 - Professional Logging
The Flight Recorder: Multi-level logging system
"""

import logging
import os
import json
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import threading

class LogLevel(Enum):
    """Log levels for different purposes"""
    INFO = "INFO"
    ERROR = "ERROR"
    DEBUG = "DEBUG"
    CRITICAL = "CRITICAL"

class ProfessionalLogger:
    """Professional logging system with multiple log levels"""
    
    def __init__(self):
        self.loggers = {}
        self.log_files = {
            LogLevel.INFO: 'logs/info.log',
            LogLevel.ERROR: 'logs/error.log',
            LogLevel.DEBUG: 'logs/debug.log'
        }
        self.log_lock = threading.Lock()
        
        # Setup all loggers
        self._setup_loggers()
        
        # Log rotation settings
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        
    def _setup_loggers(self):
        """Setup separate loggers for different levels"""
        os.makedirs('logs', exist_ok=True)
        
        for level in LogLevel:
            logger_name = f'uota_{level.value.lower()}'
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            
            # Clear existing handlers
            logger.handlers.clear()
            
            # File handler with rotation
            file_handler = logging.FileHandler(self.log_files[level])
            file_handler.setLevel(logging.INFO)
            
            # Console handler (only for errors and critical)
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setLevel(logging.INFO)
                logger.addHandler(console_handler)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(formatter)
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            
            self.loggers[level] = logger
    
    def _rotate_log_file(self, level: LogLevel):
        """Rotate log file if it's too large"""
        try:
            log_file = self.log_files[level]
            
            if not os.path.exists(log_file):
                return
            
            file_size = os.path.getsize(log_file)
            
            if file_size > self.max_file_size:
                # Rotate files
                for i in range(self.backup_count - 1, 0, -1):
                    old_file = f"{log_file}.{i}"
                    new_file = f"{log_file}.{i + 1}"
                    
                    if os.path.exists(old_file):
                        if os.path.exists(new_file):
                            os.remove(new_file)
                        os.rename(old_file, new_file)
                
                # Move current file to .1
                backup_file = f"{log_file}.1"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(log_file, backup_file)
                
                self._get_logger(level).info(f"📦 Log file rotated: {log_file}")
                
        except Exception as e:
            self._get_logger(LogLevel.ERROR).error(f"❌ Error rotating log file: {e}")
    
    def _get_logger(self, level: LogLevel):
        """Get logger for specific level"""
        return self.loggers.get(level, self.loggers[LogLevel.INFO])
    
    def log_info(self, message: str, extra_data: Dict = None):
        """Log info level message"""
        try:
            with self.log_lock:
                logger = self._get_logger(LogLevel.INFO)
                
                # Format message with extra data
                if extra_data:
                    formatted_message = f"{message} | {json.dumps(extra_data)}"
                else:
                    formatted_message = message
                
                logger.info(formatted_message)
                
                # Check rotation
                self._rotate_log_file(LogLevel.INFO)
                
        except Exception as e:
            print(f"❌ Error logging info: {e}")
    
    def log_error(self, message: str, error_data: Dict = None):
        """Log error level message"""
        try:
            with self.log_lock:
                logger = self._get_logger(LogLevel.ERROR)
                
                # Format error message
                if error_data:
                    formatted_message = f"🚨 {message} | {json.dumps(error_data)}"
                else:
                    formatted_message = f"🚨 {message}"
                
                logger.error(formatted_message)
                
                # Check rotation
                self._rotate_log_file(LogLevel.ERROR)
                
        except Exception as e:
            print(f"❌ Error logging error: {e}")
    
    def log_debug(self, message: str, debug_data: Dict = None):
        """Log debug level message"""
        try:
            with self.log_lock:
                logger = self._get_logger(LogLevel.DEBUG)
                
                # Format debug message
                if debug_data:
                    formatted_message = f"🔍 {message} | {json.dumps(debug_data)}"
                else:
                    formatted_message = f"🔍 {message}"
                
                logger.debug(formatted_message)
                
                # Check rotation
                self._rotate_log_file(LogLevel.DEBUG)
                
        except Exception as e:
            print(f"❌ Error logging debug: {e}")
    
    def log_trade_activity(self, action: str, trade_data: Dict):
        """Log trade activity"""
        try:
            trade_log = {
                'timestamp': datetime.now().isoformat(),
                'action': action,
                'trade': trade_data
            }
            
            self.log_info(f"📈 TRADE {action}", trade_log)
            
        except Exception as e:
            self.log_error(f"Error logging trade activity: {e}", {'trade_data': trade_data})
    
    def log_balance_update(self, balance: float, equity: float, margin: float):
        """Log balance update"""
        try:
            balance_log = {
                'timestamp': datetime.now().isoformat(),
                'balance': balance,
                'equity': equity,
                'margin': margin,
                'free_margin': equity - margin,
                'margin_level': (equity / margin * 100) if margin > 0 else 0
            }
            
            self.log_info(f"💰 BALANCE UPDATE", balance_log)
            
        except Exception as e:
            self.log_error(f"Error logging balance update: {e}")
    
    def log_smc_analysis(self, analysis_data: Dict):
        """Log SMC analysis with detailed math"""
        try:
            smc_log = {
                'timestamp': datetime.now().isoformat(),
                'symbol': analysis_data.get('symbol', ''),
                'timeframe': analysis_data.get('timeframe', ''),
                'liquidity_sweep': analysis_data.get('liquidity_sweep', {}),
                'order_block': analysis_data.get('order_block', {}),
                'market_structure': analysis_data.get('market_structure', {}),
                'confidence_score': analysis_data.get('confidence_score', 0),
                'entry_signal': analysis_data.get('entry_signal', ''),
                'risk_reward': analysis_data.get('risk_reward', {}),
                'math_calculations': analysis_data.get('math_calculations', {})
            }
            
            self.log_debug(f"🧠 SMC ANALYSIS", smc_log)
            
        except Exception as e:
            self.log_error(f"Error logging SMC analysis: {e}", {'analysis_data': analysis_data})
    
    def log_connection_event(self, event: str, connection_data: Dict):
        """Log connection event"""
        try:
            connection_log = {
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'server': connection_data.get('server', ''),
                'status': connection_data.get('status', ''),
                'latency_ms': connection_data.get('latency_ms', 0),
                'error_code': connection_data.get('error_code', ''),
                'retry_count': connection_data.get('retry_count', 0)
            }
            
            if event in ['CONNECTED', 'RECONNECTED']:
                self.log_info(f"🌐 CONNECTION {event}", connection_log)
            else:
                self.log_error(f"🌐 CONNECTION {event}", connection_log)
                
        except Exception as e:
            self.log_error(f"Error logging connection event: {e}", {'connection_data': connection_data})
    
    def log_system_event(self, event: str, system_data: Dict):
        """Log system event"""
        try:
            system_log = {
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'cpu_usage': system_data.get('cpu_usage', 0),
                'memory_usage_mb': system_data.get('memory_usage_mb', 0),
                'disk_usage_percent': system_data.get('disk_usage_percent', 0),
                'active_processes': system_data.get('active_processes', 0),
                'uptime_seconds': system_data.get('uptime_seconds', 0)
            }
            
            if event in ['STARTUP', 'RESTART', 'SHUTDOWN']:
                self.log_info(f"🔄 SYSTEM {event}", system_log)
            else:
                self.log_debug(f"🔄 SYSTEM {event}", system_log)
                
        except Exception as e:
            self.log_error(f"Error logging system event: {e}", {'system_data': system_data})
    
    def log_security_event(self, event: str, security_data: Dict):
        """Log security event"""
        try:
            security_log = {
                'timestamp': datetime.now().isoformat(),
                'event': event,
                'user_id': security_data.get('user_id', ''),
                'ip_address': security_data.get('ip_address', ''),
                'action': security_data.get('action', ''),
                'result': security_data.get('result', ''),
                'threat_level': security_data.get('threat_level', 'LOW')
            }
            
            self.log_error(f"🛡️ SECURITY {event}", security_log)
            
        except Exception as e:
            self.log_error(f"Error logging security event: {e}", {'security_data': security_data})
    
    def get_log_statistics(self) -> Dict:
        """Get log statistics"""
        try:
            stats = {}
            
            for level in LogLevel:
                log_file = self.log_files[level]
                
                if os.path.exists(log_file):
                    file_size = os.path.getsize(log_file)
                    
                    # Count lines
                    with open(log_file, 'r') as f:
                        line_count = sum(1 for _ in f)
                    
                    stats[level.value.lower()] = {
                        'file_size_bytes': file_size,
                        'line_count': line_count,
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(log_file)).isoformat()
                    }
                else:
                    stats[level.value.lower()] = {
                        'file_size_bytes': 0,
                        'line_count': 0,
                        'last_modified': None
                    }
            
            return stats
            
        except Exception as e:
            self.log_error(f"Error getting log statistics: {e}")
            return {}
    
    def cleanup_old_logs(self, days: int = 7):
        """Clean up old log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for level in LogLevel:
                log_file = self.log_files[level]
                
                if os.path.exists(log_file):
                    # Check backup files
                    for i in range(1, self.backup_count + 1):
                        backup_file = f"{log_file}.{i}"
                        
                        if os.path.exists(backup_file):
                            mod_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
                            
                            if mod_time < cutoff_date:
                                os.remove(backup_file)
                                self.log_info(f"🗑️ Removed old log backup: {backup_file}")
            
        except Exception as e:
            self.log_error(f"Error cleaning up old logs: {e}")
    
    def replace_print_statements(self):
        """Replace all print statements with logging"""
        try:
            self.log_info("🔧 Replacing print statements with logging...")
            
            # Find all Python files
            python_files = []
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(os.path.join(root, file))
            
            replacements_made = 0
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Replace print statements
                    content = content.replace('print(', 'self.logger.info(')
                    content = content.replace('print(', 'self.logger.debug(')
                    
                    # Replace print without parentheses (Python 2 style)
                    content = content.replace('print ', 'self.logger.info(')
                    
                    # Write back if changed
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        replacements_made += 1
                        self.log_debug(f"🔧 Replaced print statements in: {file_path}")
                
                except Exception as e:
                    self.log_error(f"Error replacing print in {file_path}: {e}")
            
            self.log_info(f"✅ Print statement replacement complete: {replacements_made} files modified")
            
        except Exception as e:
            self.log_error(f"Error replacing print statements: {e}")

# Global professional logger instance
professional_logger = ProfessionalLogger()

# Convenience functions for easy access
def log_info(message: str, extra_data: Dict = None):
    """Log info message"""
    professional_logger.log_info(message, extra_data)

def log_error(message: str, error_data: Dict = None):
    """Log error message"""
    professional_logger.log_error(message, error_data)

def log_debug(message: str, debug_data: Dict = None):
    """Log debug message"""
    professional_logger.log_debug(message, debug_data)

def log_trade_activity(action: str, trade_data: Dict):
    """Log trade activity"""
    professional_logger.log_trade_activity(action, trade_data)

def log_balance_update(balance: float, equity: float, margin: float):
    """Log balance update"""
    professional_logger.log_balance_update(balance, equity, margin)

def log_smc_analysis(analysis_data: Dict):
    """Log SMC analysis"""
    professional_logger.log_smc_analysis(analysis_data)

def log_connection_event(event: str, connection_data: Dict):
    """Log connection event"""
    professional_logger.log_connection_event(event, connection_data)

def log_system_event(event: str, system_data: Dict):
    """Log system event"""
    professional_logger.log_system_event(event, system_data)

def log_security_event(event: str, security_data: Dict):
    """Log security event"""
    professional_logger.log_security_event(event, security_data)
