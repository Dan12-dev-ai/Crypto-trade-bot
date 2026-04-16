"""
UOTA Elite v2 - Automated Logging System
Structured logging for signals, trades, and system events
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import os  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
# import aiofiles  # Moved to function to avoid circular import
# import traceback  # Moved to function to avoid circular import
from pathlib import Path

class LogLevel(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(Enum):
    SIGNAL = "signal"
    TRADE = "trade"
    SYSTEM = "system"
    RISK = "risk"
    PERFORMANCE = "performance"
    CONNECTION = "connection"
    VALIDATION = "validation"
    EXECUTION = "execution"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    component: str
    message: str
    metadata: Optional[Dict[str, Any]]
    session_id: str
    correlation_id: Optional[str] = None

class AutomatedLoggingSystem:
    """Comprehensive automated logging system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session_id = f"session_{int(datetime.now().timestamp())}"
        self.log_buffer = []
        self.is_running = False
        
        # Logging configuration
        self.config = {
            'buffer_size': 1000,           # Max entries in buffer
            'flush_interval': 30,           # Seconds between flushes
            'max_log_files': 7,             # Days to keep logs
            'log_directory': 'logs/structured',
            'enable_console_output': True,
            'enable_file_output': True,
            'enable_json_format': True,
            'compression_enabled': True
        }
        
        # Log file paths
        self.log_files = {
            category: f"{self.config['log_directory']}/{category.value}.log"
            for category in LogCategory
        }
        
        # Statistics
        self.stats = {
            'total_logs': 0,
            'logs_by_level': {level.value: 0 for level in LogLevel},
            'logs_by_category': {category.value: 0 for category in LogCategory},
            'buffer_overflows': 0,
            'flush_errors': 0,
            'session_start': datetime.now().isoformat()
        }
        
        # Setup logging infrastructure
        self._setup_logging_infrastructure()
    
    def _setup_logging_infrastructure(self):
        """Setup logging directories and files"""
        try:
            # Create log directory
            Path(self.config['log_directory']).mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories
            for category in LogCategory:
                category_dir = f"{self.config['log_directory']}/{category.value}"
                Path(category_dir).mkdir(parents=True, exist_ok=True)
            
            self.logger.info("✅ Logging infrastructure initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Error setting up logging infrastructure: {e}")
    
    async def start_logging(self):
        """Start automated logging system"""
        try:
            self.is_running = True
            self.logger.info("📝 Starting Automated Logging System...")
            
            # Start background flush task
            flush_task = asyncio.create_task(self._background_flush())
            
            # Start cleanup task
            cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            # Log system startup
            await self.log_system_event(
                component="AutomatedLoggingSystem",
                message="Logging system started",
                metadata={'session_id': self.session_id}
            )
            
            # Wait for tasks
            await asyncio.gather(flush_task, cleanup_task, return_exceptions=True)
            
        except Exception as e:
            self.logger.error(f"❌ Error starting logging system: {e}")
            self.is_running = False
    
    async def log_signal(self, symbol: str, signal_type: str, confidence: float,
                       entry_price: float, stop_loss: float, take_profit: float,
                       metadata: Optional[Dict[str, Any]] = None):
        """Log trading signal"""
        try:
            await self._log_entry(
                level=LogLevel.INFO,
                category=LogCategory.SIGNAL,
                component="SignalGenerator",
                message=f"Signal generated: {symbol} {signal_type} confidence={confidence:.2f}",
                metadata={
                    'symbol': symbol,
                    'signal_type': signal_type,
                    'confidence': confidence,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    **(metadata or {})
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging signal: {e}")
    
    async def log_trade(self, action: str, symbol: str, volume: float, price: float,
                       order_ticket: Optional[int] = None, slippage: Optional[float] = None,
                       metadata: Optional[Dict[str, Any]] = None):
        """Log trade execution"""
        try:
            await self._log_entry(
                level=LogLevel.INFO,
                category=LogCategory.TRADE,
                component="TradeExecutor",
                message=f"Trade {action}: {symbol} {volume} lots @ {price}",
                metadata={
                    'action': action,
                    'symbol': symbol,
                    'volume': volume,
                    'price': price,
                    'order_ticket': order_ticket,
                    'slippage': slippage,
                    **(metadata or {})
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging trade: {e}")
    
    async def log_system_event(self, component: str, message: str,
                             level: LogLevel = LogLevel.INFO,
                             metadata: Optional[Dict[str, Any]] = None):
        """Log system event"""
        try:
            await self._log_entry(
                level=level,
                category=LogCategory.SYSTEM,
                component=component,
                message=message,
                metadata=metadata
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging system event: {e}")
    
    async def log_risk_event(self, risk_type: str, severity: str, description: str,
                           current_value: Optional[float] = None,
                           threshold: Optional[float] = None,
                           metadata: Optional[Dict[str, Any]] = None):
        """Log risk management event"""
        try:
            level = LogLevel.WARNING if severity == "warning" else LogLevel.CRITICAL
            
            await self._log_entry(
                level=level,
                category=LogCategory.RISK,
                component="RiskManager",
                message=f"Risk event: {risk_type} - {severity} - {description}",
                metadata={
                    'risk_type': risk_type,
                    'severity': severity,
                    'description': description,
                    'current_value': current_value,
                    'threshold': threshold,
                    **(metadata or {})
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging risk event: {e}")
    
    async def log_performance_metric(self, metric_name: str, value: float,
                                    unit: str, metadata: Optional[Dict[str, Any]] = None):
        """Log performance metric"""
        try:
            await self._log_entry(
                level=LogLevel.INFO,
                category=LogCategory.PERFORMANCE,
                component="PerformanceMonitor",
                message=f"Performance metric: {metric_name} = {value} {unit}",
                metadata={
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    **(metadata or {})
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging performance metric: {e}")
    
    async def log_connection_event(self, service: str, status: str,
                                 latency_ms: Optional[float] = None,
                                 metadata: Optional[Dict[str, Any]] = None):
        """Log connection event"""
        try:
            level = LogLevel.INFO if status == "connected" else LogLevel.WARNING
            
            await self._log_entry(
                level=level,
                category=LogCategory.CONNECTION,
                component="ConnectionManager",
                message=f"Connection event: {service} - {status}",
                metadata={
                    'service': service,
                    'status': status,
                    'latency_ms': latency_ms,
                    **(metadata or {})
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging connection event: {e}")
    
    async def log_validation_result(self, validator: str, target: str, result: bool,
                                   score: Optional[float] = None,
                                   issues: Optional[List[str]] = None,
                                   metadata: Optional[Dict[str, Any]] = None):
        """Log validation result"""
        try:
            level = LogLevel.INFO if result else LogLevel.WARNING
            
            await self._log_entry(
                level=level,
                category=LogCategory.VALIDATION,
                component=validator,
                message=f"Validation result: {target} - {'PASSED' if result else 'FAILED'}",
                metadata={
                    'validator': validator,
                    'target': target,
                    'result': result,
                    'score': score,
                    'issues': issues or [],
                    **(metadata or {})
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging validation result: {e}")
    
    async def log_execution_event(self, request_id: str, status: str,
                                execution_time_ms: Optional[float] = None,
                                error_message: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None):
        """Log execution event"""
        try:
            level = LogLevel.INFO if status == "success" else LogLevel.ERROR
            
            await self._log_entry(
                level=level,
                category=LogCategory.EXECUTION,
                component="ExecutionEngine",
                message=f"Execution event: {request_id} - {status}",
                metadata={
                    'request_id': request_id,
                    'status': status,
                    'execution_time_ms': execution_time_ms,
                    'error_message': error_message,
                    **(metadata or {})
                }
            )
        except Exception as e:
            self.logger.error(f"❌ Error logging execution event: {e}")
    
    async def _log_entry(self, level: LogLevel, category: LogCategory,
                        component: str, message: str,
                        metadata: Optional[Dict[str, Any]] = None):
        """Internal log entry method"""
        try:
            # Create log entry
            entry = LogEntry(
                timestamp=datetime.now(),
                level=level,
                category=category,
                component=component,
                message=message,
                metadata=metadata,
                session_id=self.session_id
            )
            
            # Add to buffer
            self.log_buffer.append(entry)
            
            # Update statistics
            self.stats['total_logs'] += 1
            self.stats['logs_by_level'][level.value] += 1
            self.stats['logs_by_category'][category.value] += 1
            
            # Check buffer size
            if len(self.log_buffer) > self.config['buffer_size']:
                self.stats['buffer_overflows'] += 1
                # Remove oldest entries
                self.log_buffer = self.log_buffer[-self.config['buffer_size']:]
            
            # Console output if enabled
            if self.config['enable_console_output']:
                self._console_output(entry)
                
        except Exception as e:
            self.logger.error(f"❌ Error creating log entry: {e}")
    
    def _console_output(self, entry: LogEntry):
        """Output log entry to console"""
        try:
            # Format console message
            timestamp = entry.timestamp.strftime('%H:%M:%S')
            level_symbol = {
                LogLevel.DEBUG: "🔍",
                LogLevel.INFO: "ℹ️",
                LogLevel.WARNING: "⚠️",
                LogLevel.ERROR: "❌",
                LogLevel.CRITICAL: "🚨"
            }.get(entry.level, "📝")
            
            category_symbol = {
                LogCategory.SIGNAL: "🎯",
                LogCategory.TRADE: "💰",
                LogCategory.SYSTEM: "⚙️",
                LogCategory.RISK: "🛡️",
                LogCategory.PERFORMANCE: "📊",
                LogCategory.CONNECTION: "🔗",
                LogCategory.VALIDATION: "✅",
                LogCategory.EXECUTION: "🚀"
            }.get(entry.category, "📋")
            
            console_message = f"{timestamp} {level_symbol} {category_symbol} [{entry.component}] {entry.message}"
            
            # Print with appropriate color (if supported)
            if sys.stdout.isatty():
                color_code = {
                    LogLevel.DEBUG: "\033[36m",      # Cyan
                    LogLevel.INFO: "\033[32m",       # Green
                    LogLevel.WARNING: "\033[33m",     # Yellow
                    LogLevel.ERROR: "\033[31m",       # Red
                    LogLevel.CRITICAL: "\033[35m"     # Magenta
                }.get(entry.level, "\033[0m")
                
                reset_code = "\033[0m"
                print(f"{color_code}{console_message}{reset_code}")
            else:
                print(console_message)
                
        except Exception as e:
            self.logger.error(f"❌ Error in console output: {e}")
    
    async def _background_flush(self):
        """Background task to flush logs to files"""
        try:
            while self.is_running:
                try:
                    await self._flush_logs()
                    await asyncio.sleep(self.config['flush_interval'])
                except Exception as e:
                    self.logger.error(f"❌ Error in background flush: {e}")
                    self.stats['flush_errors'] += 1
                    await asyncio.sleep(5)  # Short delay before retry
                    
        except Exception as e:
            self.logger.error(f"❌ Critical error in background flush: {e}")
    
    async def _flush_logs(self):
        """Flush log buffer to files"""
        try:
            if not self.log_buffer:
                return
            
            # Get entries to flush
            entries_to_flush = self.log_buffer.copy()
            self.log_buffer.clear()
            
            # Group by category
            entries_by_category = {}
            for entry in entries_to_flush:
                if entry.category not in entries_by_category:
                    entries_by_category[entry.category] = []
                entries_by_category[entry.category].append(entry)
            
            # Write to category-specific files
            for category, entries in entries_by_category.items():
                await self._write_category_logs(category, entries)
                
        except Exception as e:
            self.logger.error(f"❌ Error flushing logs: {e}")
            self.stats['flush_errors'] += 1
    
    async def _write_category_logs(self, category: LogCategory, entries: List[LogEntry]):
        """Write logs to category-specific file"""
        try:
            # Create daily log file
            date_str = datetime.now().strftime('%Y-%m-%d')
            log_file = f"{self.config['log_directory']}/{category.value}/{date_str}.json"
            
            # Read existing logs
            existing_logs = []
            if os.path.exists(log_file):
                async with aiofiles.open(log_file, 'r') as f:
                    content = await f.read()
                    if content:
                        existing_logs = json.loads(content)
            
            # Convert entries to dictionaries
            new_logs = []
            for entry in entries:
                entry_dict = asdict(entry)
                entry_dict['timestamp'] = entry.timestamp.isoformat()
                entry_dict['level'] = entry.level.value
                entry_dict['category'] = entry.category.value
                new_logs.append(entry_dict)
            
            # Combine and save
            all_logs = existing_logs + new_logs
            
            # Keep only last 24 hours of logs
            cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
            all_logs = [log for log in all_logs if log['timestamp'] > cutoff_time]
            
            # Write to file
            async with aiofiles.open(log_file, 'w') as f:
                await f.write(json.dumps(all_logs, indent=2))
                
        except Exception as e:
            self.logger.error(f"❌ Error writing category logs: {e}")
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old log files"""
        try:
            while self.is_running:
                try:
                    await self._cleanup_old_logs()
                    # Run cleanup every 24 hours
                    await asyncio.sleep(86400)
                except Exception as e:
                    self.logger.error(f"❌ Error in periodic cleanup: {e}")
                    await asyncio.sleep(3600)  # Retry after 1 hour
                    
        except Exception as e:
            self.logger.error(f"❌ Critical error in periodic cleanup: {e}")
    
    async def _cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config['max_log_files'])
            
            for category in LogCategory:
                category_dir = f"{self.config['log_directory']}/{category.value}"
                if os.path.exists(category_dir):
                    for filename in os.listdir(category_dir):
                        file_path = os.path.join(category_dir, filename)
                        if os.path.isfile(file_path):
                            # Check file modification time
                            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                            if file_time < cutoff_date:
                                os.remove(file_path)
                                self.logger.debug(f"🗑️ Removed old log file: {file_path}")
                                
        except Exception as e:
            self.logger.error(f"❌ Error cleaning up old logs: {e}")
    
    async def search_logs(self, query: str, category: Optional[LogCategory] = None,
                         level: Optional[LogLevel] = None,
                         start_time: Optional[datetime] = None,
                         end_time: Optional[datetime] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Search logs with filters"""
        try:
            results = []
            
            # Determine which files to search
            if category:
                categories = [category]
            else:
                categories = list(LogCategory)
            
            for cat in categories:
                category_dir = f"{self.config['log_directory']}/{cat.value}"
                if os.path.exists(category_dir):
                    for filename in os.listdir(category_dir):
                        if filename.endswith('.json'):
                            file_path = os.path.join(category_dir, filename)
                            
                            # Read log file
                            async with aiofiles.open(file_path, 'r') as f:
                                content = await f.read()
                                if content:
                                    logs = json.loads(content)
                                    
                                    # Filter logs
                                    for log in logs:
                                        # Time filter
                                        log_time = datetime.fromisoformat(log['timestamp'])
                                        if start_time and log_time < start_time:
                                            continue
                                        if end_time and log_time > end_time:
                                            continue
                                        
                                        # Level filter
                                        if level and log['level'] != level.value:
                                            continue
                                        
                                        # Text search
                                        if query.lower() in log['message'].lower():
                                            results.append(log)
                                            
                                            if len(results) >= limit:
                                                return results
            
            return results[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Error searching logs: {e}")
            return []
    
    def get_logging_statistics(self) -> Dict[str, Any]:
        """Get logging system statistics"""
        try:
            return {
                'session_id': self.session_id,
                'is_running': self.is_running,
                'buffer_size': len(self.log_buffer),
                'max_buffer_size': self.config['buffer_size'],
                'statistics': self.stats,
                'configuration': self.config,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting logging statistics: {e}")
            return {'error': str(e)}
    
    async def export_logs(self, start_time: datetime, end_time: datetime,
                         categories: Optional[List[LogCategory]] = None,
                         format: str = 'json') -> str:
        """Export logs to file"""
        try:
            # Collect logs
            all_logs = []
            
            search_categories = categories or list(LogCategory)
            
            for category in search_categories:
                logs = await self.search_logs(
                    query="",
                    category=category,
                    start_time=start_time,
                    end_time=end_time,
                    limit=10000
                )
                all_logs.extend(logs)
            
            # Sort by timestamp
            all_logs.sort(key=lambda x: x['timestamp'])
            
            # Create export file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_file = f"{self.config['log_directory']}/export_{timestamp}.{format}"
            
            if format == 'json':
                async with aiofiles.open(export_file, 'w') as f:
                    await f.write(json.dumps(all_logs, indent=2))
            elif format == 'csv':
                # Convert to CSV format
                # import csv  # Moved to function to avoid circular import
                if all_logs:
                    fields = ['timestamp', 'level', 'category', 'component', 'message']
                    async with aiofiles.open(export_file, 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fields)
                        await f.write(','.join(fields) + '\n')
                        for log in all_logs:
                            row = {field: log.get(field, '') for field in fields}
                            await f.write(','.join(str(v) for v in row.values()) + '\n')
            
            self.logger.info(f"📤 Logs exported to: {export_file}")
            return export_file
            
        except Exception as e:
            self.logger.error(f"❌ Error exporting logs: {e}")
            return ""
    
    def stop_logging(self):
        """Stop logging system"""
        try:
            self.is_running = False
            
            # Flush remaining logs
            if self.log_buffer:
                asyncio.create_task(self._flush_logs())
            
            self.logger.info("📝 Automated Logging System stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping logging system: {e}")

# Global logging system instance
automated_logging_system = AutomatedLoggingSystem()
