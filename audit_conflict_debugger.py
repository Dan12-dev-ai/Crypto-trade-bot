#!/usr/bin/env python3
"""
UOTA Elite v2 - Deep Conflict Debugger
Race condition detection and NoneType error prevention
"""

# import asyncio  # Moved to function to avoid circular import
# import threading  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import inspect  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
# import psutil  # Moved to function to avoid circular import
# import gc  # Moved to function to avoid circular import

class ConflictDebugger:
    """Deep conflict debugging system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.order_lock = threading.Lock()
        self.last_order_time = 0
        self.order_buffer = []
        self.race_conditions_detected = []
        self.nonetype_errors = []
        self.memory_snapshots = []
        
        # Thread safety monitoring
        self.active_threads = {}
        self.thread_locks = {}
        
    def scan_file_for_race_conditions(self, file_path: str) -> Dict:
        """Scan file for potential race conditions"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            issues = {
                'file': file_path,
                'race_conditions': [],
                'nonetype_risks': [],
                'thread_safety_issues': [],
                'concurrent_access': []
            }
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                # Check for race condition patterns
                race_patterns = [
                    'asyncio.gather(',
                    'asyncio.create_task(',
                    'threading.Thread(',
                    'ThreadPoolExecutor(',
                    'concurrent.futures',
                    'multiprocessing'
                ]
                
                for pattern in race_patterns:
                    if pattern in line:
                        issues['race_conditions'].append({
                            'line': i,
                            'code': line.strip(),
                            'pattern': pattern,
                            'severity': 'HIGH'
                        })
                
                # Check for NoneType risks
                nonetype_patterns = [
                    '.split(',
                    '.strip(',
                    '.lower(',
                    '.upper(',
                    '.get(',
                    '[0]',
                    '[1]',
                    '.price',
                    '.volume',
                    '.symbol'
                ]
                
                for pattern in nonetype_patterns:
                    if pattern in line and 'if' not in line and 'try:' not in line:
                        issues['nonetype_risks'].append({
                            'line': i,
                            'code': line.strip(),
                            'pattern': pattern,
                            'severity': 'MEDIUM'
                        })
                
                # Check for thread safety issues
                thread_patterns = [
                    'global ',
                    'nonlocal ',
                    'shared_',
                    'cache_',
                    'buffer_'
                ]
                
                for pattern in thread_patterns:
                    if pattern in line:
                        issues['thread_safety_issues'].append({
                            'line': i,
                            'code': line.strip(),
                            'pattern': pattern,
                            'severity': 'HIGH'
                        })
            
            return issues
            
        except Exception as e:
            self.logger.error(f"❌ Error scanning {file_path}: {e}")
            return {'file': file_path, 'error': str(e)}
    
    def prevent_duplicate_orders(self, order_data: Dict) -> bool:
        """Prevent duplicate orders in same millisecond"""
        try:
            with self.order_lock:
                current_time = time.time() * 1000  # Convert to milliseconds
                
                # Check if same order was placed in last millisecond
                if self.last_order_time and (current_time - self.last_order_time) < 1:
                    self.logger.warning(f"🚨 RACE CONDITION DETECTED: Duplicate order prevented")
                    self.race_conditions_detected.append({
                        'timestamp': datetime.now().isoformat(),
                        'order_data': order_data,
                        'time_diff_ms': current_time - self.last_order_time
                    })
                    return False
                
                # Check order buffer for duplicates
                for buffered_order in self.order_buffer[-10:]:  # Check last 10 orders
                    if (buffered_order.get('symbol') == order_data.get('symbol') and
                        buffered_order.get('type') == order_data.get('type') and
                        abs(buffered_order.get('price', 0) - order_data.get('price', 0)) < 0.001):
                        self.logger.warning(f"🚨 DUPLICATE ORDER DETECTED: Same symbol/price in buffer")
                        return False
                
                # Update last order time and buffer
                self.last_order_time = current_time
                self.order_buffer.append({
                    'timestamp': current_time,
                    'order_data': order_data
                })
                
                # Keep buffer size manageable
                if len(self.order_buffer) > 100:
                    self.order_buffer = self.order_buffer[-50:]
                
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error in duplicate order prevention: {e}")
            return False
    
    def safe_mt5_data_access(self, data, operation: str = 'get') -> Any:
        """Safe MT5 data access with NoneType protection"""
        try:
            if data is None:
                self.nonetype_errors.append({
                    'timestamp': datetime.now().isoformat(),
                    'operation': operation,
                    'error': 'MT5 returned None data',
                    'data_type': type(data)
                })
                self.logger.warning(f"⚠️ MT5 returned None for {operation}")
                return None
            
            # Check for empty data structures
            if hasattr(data, '__len__') and len(data) == 0:
                self.logger.warning(f"⚠️ MT5 returned empty data for {operation}")
                return None
            
            # Safe attribute access
            if operation == 'price':
                if hasattr(data, 'bid') and data.bid is not None:
                    return data.bid
                elif hasattr(data, 'ask') and data.ask is not None:
                    return data.ask
                elif isinstance(data, dict) and 'price' in data and data['price'] is not None:
                    return data['price']
                else:
                    self.nonetype_errors.append({
                        'timestamp': datetime.now().isoformat(),
                        'operation': operation,
                        'error': 'Price data is None',
                        'data': str(data)[:100]
                    })
                    return None
            
            elif operation == 'volume':
                if hasattr(data, 'volume') and data.volume is not None:
                    return data.volume
                elif isinstance(data, dict) and 'volume' in data and data['volume'] is not None:
                    return data['volume']
                else:
                    self.nonetype_errors.append({
                        'timestamp': datetime.now().isoformat(),
                        'operation': operation,
                        'error': 'Volume data is None',
                        'data': str(data)[:100]
                    })
                    return None
            
            elif operation == 'symbol':
                if hasattr(data, 'symbol') and data.symbol is not None:
                    return data.symbol
                elif isinstance(data, dict) and 'symbol' in data and data['symbol'] is not None:
                    return data['symbol']
                else:
                    self.nonetype_errors.append({
                        'timestamp': datetime.now().isoformat(),
                        'operation': operation,
                        'error': 'Symbol data is None',
                        'data': str(data)[:100]
                    })
                    return None
            
            else:
                return data
                
        except Exception as e:
            self.nonetype_errors.append({
                'timestamp': datetime.now().isoformat(),
                'operation': operation,
                'error': f'Exception: {str(e)}',
                'data': str(data)[:100] if data else 'None'
            })
            self.logger.error(f"❌ Error in safe MT5 data access: {e}")
            return None
    
    def monitor_memory_usage(self) -> Dict:
        """Monitor memory usage and detect leaks"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get memory usage
            memory_mb = memory_info.rss / 1024 / 1024
            memory_percent = process.memory_percent()
            
            # Force garbage collection
            collected = gc.collect()
            
            # Take memory snapshot
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'memory_mb': memory_mb,
                'memory_percent': memory_percent,
                'objects_collected': collected,
                'gc_stats': gc.get_stats() if hasattr(gc, 'get_stats') else []
            }
            
            self.memory_snapshots.append(snapshot)
            
            # Keep only last 100 snapshots
            if len(self.memory_snapshots) > 100:
                self.memory_snapshots = self.memory_snapshots[-50:]
            
            # Check for memory leak
            if len(self.memory_snapshots) > 10:
                recent_snapshots = self.memory_snapshots[-10:]
                memory_trend = [s['memory_mb'] for s in recent_snapshots]
                
                # Check if memory is consistently increasing
                if all(memory_trend[i] < memory_trend[i+1] for i in range(len(memory_trend)-1)):
                    self.logger.warning(f"🚨 MEMORY LEAK DETECTED: Memory consistently increasing")
                    snapshot['memory_leak_detected'] = True
            
            return snapshot
            
        except Exception as e:
            self.logger.error(f"❌ Error monitoring memory: {e}")
            return {}
    
    def get_audit_report(self) -> Dict:
        """Generate comprehensive audit report"""
        try:
            # Scan critical files
            files_to_scan = [
                'master_controller.py',
                'exchange_integration.py',
                'smc_logic_gate.py',
                'brain.py'
            ]
            
            scan_results = {}
            for file_path in files_to_scan:
                try:
                    scan_results[file_path] = self.scan_file_for_race_conditions(file_path)
                except:
                    scan_results[file_path] = {'error': 'File not found'}
            
            # Get latest memory snapshot
            latest_memory = self.memory_snapshots[-1] if self.memory_snapshots else {}
            
            report = {
                'audit_timestamp': datetime.now().isoformat(),
                'conflict_analysis': scan_results,
                'race_conditions_detected': len(self.race_conditions_detected),
                'nonetype_errors_detected': len(self.nonetype_errors),
                'memory_analysis': {
                    'current_usage_mb': latest_memory.get('memory_mb', 0),
                    'memory_percent': latest_memory.get('memory_percent', 0),
                    'memory_leak_detected': latest_memory.get('memory_leak_detected', False),
                    'objects_collected': latest_memory.get('objects_collected', 0)
                },
                'thread_safety': {
                    'active_threads': len(threading.enumerate()),
                    'order_lock_acquired': self.order_lock.locked(),
                    'last_order_time': self.last_order_time
                },
                'recommendations': self._generate_recommendations()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating audit report: {e}")
            return {'error': str(e)}
    
    def _generate_recommendations(self) -> List[str]:
        """Generate audit recommendations"""
        recommendations = []
        
        # Race condition recommendations
        if self.race_conditions_detected:
            recommendations.append("🔒 Implement stricter order timing controls")
            recommendations.append("🔒 Add order deduplication logic")
        
        # NoneType error recommendations
        if self.nonetype_errors:
            recommendations.append("🛡️ Add comprehensive NoneType checks for MT5 data")
            recommendations.append("🛡️ Implement data validation before processing")
        
        # Memory recommendations
        if self.memory_snapshots:
            latest_memory = self.memory_snapshots[-1]
            if latest_memory.get('memory_mb', 0) > 200:
                recommendations.append("🧹 Optimize data buffers to reduce memory usage")
                recommendations.append("🧹 Implement more aggressive garbage collection")
        
        # Thread safety recommendations
        if len(threading.enumerate()) > 10:
            recommendations.append("🧵 Review thread usage and implement thread pooling")
        
        return recommendations

# Global conflict debugger instance
conflict_debugger = ConflictDebugger()
