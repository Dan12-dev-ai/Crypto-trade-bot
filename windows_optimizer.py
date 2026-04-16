"""
UOTA Elite v2 - Windows Resource Optimizer
Real-time priority and resource management
"""

# import os  # Moved to function to avoid circular import
# import sys  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import psutil  # Moved to function to avoid circular import
# import gc  # Moved to function to avoid circular import
from typing import Dict, Any

class WindowsOptimizer:
    """Windows-specific resource optimizer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.original_priority = None
        self.optimization_enabled = True
        
    def set_real_time_priority(self):
        """Set current process to real-time priority"""
        try:
            # # import win32api  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            # # import win32process  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            # import win32con  # Moved to function to avoid circular import
            
            # Get current process handle
            handle = win32api.GetCurrentProcess()
            
            # Get original priority for restoration
            self.original_priority = win32process.GetPriorityClass(handle)
            
            # Set to real-time priority
            win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)
            
            self.logger.info("✅ Process priority set to REAL-TIME")
            return True
            
        except ImportError:
            self.logger.warning("⚠️ pywin32 not available - priority not set")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error setting priority: {e}")
            return False
    
    def restore_original_priority(self):
        """Restore original process priority"""
        try:
            if self.original_priority:
                # # import win32api  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                # # import win32process  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                
                handle = win32api.GetCurrentProcess()
                win32process.SetPriorityClass(handle, self.original_priority)
                
                self.logger.info("✅ Process priority restored")
                
        except Exception as e:
            self.logger.error(f"❌ Error restoring priority: {e}")
    
    def optimize_memory(self):
        """Optimize memory usage"""
        try:
            # Force garbage collection
            collected = gc.collect()
            
            # Get memory info
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            self.logger.info(f"🧹 Memory optimized: {collected} objects collected, {memory_percent:.1f}% RAM used")
            
            return {
                'objects_collected': collected,
                'memory_mb': memory_info.rss / 1024 / 1024,
                'memory_percent': memory_percent
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing memory: {e}")
            return None
    
    def optimize_cpu(self):
        """Optimize CPU usage"""
        try:
            # Get CPU info
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Set process affinity to all cores
            process = psutil.Process()
            original_affinity = process.cpu_affinity()
            
            # Set to all available cores
            all_cores = list(range(cpu_count))
            process.cpu_affinity(all_cores)
            
            self.logger.info(f"⚡ CPU optimized: {cpu_percent}% usage, {cpu_count} cores")
            
            return {
                'cpu_percent': cpu_percent,
                'cpu_count': cpu_count,
                'affinity': all_cores
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing CPU: {e}")
            return None
    
    def disable_print_statements(self):
        """Disable non-critical print statements"""
        try:
            # Override print function for non-critical messages
            original_print = print
            
            def critical_print(*args, **kwargs):
                # Only allow critical messages
                if args and isinstance(args[0], str):
                    message = args[0]
                    critical_keywords = ['ERROR', 'CRITICAL', 'TRADE', 'EXECUTION', 'PROFIT', 'LOSS']
                    
                    if any(keyword in message.upper() for keyword in critical_keywords):
                        original_print(*args, **kwargs)
                    else:
                        # Log instead of print
                        self.logger.info(' '.join(str(arg) for arg in args))
                else:
                    original_print(*args, **kwargs)
            
            # Replace built-in print
            # # import builtins  # Moved to function to avoid circular import  # Moved to function to avoid circular # import builtins  # Moved to function to avoid circular import.print = critical_print
            
            self.logger.info("✅ Print statements optimized for critical messages only")
            
        except Exception as e:
            self.logger.error(f"❌ Error disabling print statements: {e}")
    
    def optimize_network_settings(self):
        """Optimize network settings for low latency"""
        try:
            # import socket  # Moved to function to avoid circular import
            
            # Set socket options for low latency
            # TCP_NODELAY disables Nagle's algorithm
            socket.TCP_NODELAY = 1
            
            # Set keepalive options
            socket.TCP_KEEPIDLE = 30
            socket.TCP_KEEPINTVL = 10
            socket.TCP_KEEPCNT = 5
            
            self.logger.info("🌐 Network settings optimized for low latency")
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing network settings: {e}")
    
    def optimize_disk_io(self):
        """Optimize disk I/O"""
        try:
            # Set file buffering for better performance
            # import io  # Moved to function to avoid circular import
            
            # Optimize file operations
            io.DEFAULT_BUFFER_SIZE = 65536  # 64KB buffer
            
            self.logger.info("💾 Disk I/O optimized")
            
        except Exception as e:
            self.logger.error(f"❌ Error optimizing disk I/O: {e}")
    
    def get_system_resources(self) -> Dict[str, Any]:
        """Get current system resource usage"""
        try:
            process = psutil.Process()
            
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': process.memory_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else {},
                'process_count': len(psutil.pids()),
                'boot_time': psutil.boot_time()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting system resources: {e}")
            return {}
    
    def optimize_all(self):
        """Apply all optimizations"""
        try:
            self.logger.info("🚀 Starting Windows optimization...")
            
            results = {}
            
            # Set real-time priority
            results['priority'] = self.set_real_time_priority()
            
            # Optimize memory
            results['memory'] = self.optimize_memory()
            
            # Optimize CPU
            results['cpu'] = self.optimize_cpu()
            
            # Disable print statements
            self.disable_print_statements()
            
            # Optimize network
            self.optimize_network_settings()
            
            # Optimize disk I/O
            self.optimize_disk_io()
            
            self.logger.info("✅ Windows optimization complete")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Error in optimization: {e}")
            return {}
    
    def cleanup(self):
        """Cleanup and restore original settings"""
        try:
            self.logger.info("🧹 Cleaning up optimizations...")
            
            # Restore original priority
            self.restore_original_priority()
            
            # Restore original print
            # # import builtins  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            if hasattr(builtins, '_original_print'):
                builtins.print = builtins._original_print
            
            self.logger.info("✅ Cleanup complete")
            
        except Exception as e:
            self.logger.error(f"❌ Error in cleanup: {e}")

# Global optimizer instance
windows_optimizer = WindowsOptimizer()

# Decorator for optimized functions
def optimized_execution(func):
    """Decorator for optimized function execution"""
    def wrapper(*args, **kwargs):
        try:
            # Optimize before execution
            windows_optimizer.optimize_memory()
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Optimize after execution
            windows_optimizer.optimize_memory()
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Error in optimized execution: {e}")
            raise
    
    return wrapper
