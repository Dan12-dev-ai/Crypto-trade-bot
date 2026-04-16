"""
Crypto trade bot - Zero-Downtime Infrastructure Optimizations
Async connection handlers and persistent warm connections
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import aiohttp  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
# import json  # Moved to function to avoid circular import
from pathlib import Path

class ConnectionStatus(Enum):
    """Connection status states"""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"

@dataclass
class ConnectionMetrics:
    """Connection performance metrics"""
    status: ConnectionStatus
    last_ping: datetime
    latency_ms: float
    uptime_percentage: float
    reconnect_count: int
    error_count: int
    bytes_sent: int
    bytes_received: int

class AsyncConnectionManager:
    """High-performance async connection manager with warm connections"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connections: Dict[str, Dict] = {}
        self.connection_pools: Dict[str, aiohttp.TCPConnector] = {}
        self.heartbeat_interval = 0.05  # 50ms heartbeat
        self.warm_connection_timeout = 300  # 5 minutes
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 0.1  # 100ms initial delay
        
    async def initialize(self):
        """Initialize connection manager"""
        try:
            # Start connection monitoring
            asyncio.create_task(self._connection_monitor())
            
            # Start heartbeat maintenance
            asyncio.create_task(self._heartbeat_maintenance())
            
            self.logger.info("🚀 Zero-downtime connection manager initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing connection manager: {e}")
            raise
            
    async def create_warm_connection(self, exchange_name: str, api_config: Dict) -> bool:
        """Create and maintain warm connection to exchange"""
        try:
            # Create connection pool
            connector = aiohttp.TCPConnector(
                limit=100,  # Max connections
                limit_per_host=20,  # Per-host limit
                ttl_dns_cache=300,  # 5 minute DNS cache
                use_dns_cache=True,
                keepalive_timeout=30,  # 30 second keepalive
                enable_cleanup_closed=True
            )
            
            # Create session with optimized settings
            timeout = aiohttp.ClientTimeout(
                total=5.0,  # 5 second total timeout
                connect=1.0,  # 1 second connect timeout
                sock_read=2.0  # 2 second read timeout
            )
            
            session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'UOTA-Elite-v2/1.0',
                    'Connection': 'keep-alive'
                }
            )
            
            # Store connection
            self.connections[exchange_name] = {
                'session': session,
                'connector': connector,
                'api_config': api_config,
                'created_at': datetime.now(),
                'last_used': datetime.now(),
                'metrics': ConnectionMetrics(
                    status=ConnectionStatus.CONNECTING,
                    last_ping=datetime.now(),
                    latency_ms=0.0,
                    uptime_percentage=0.0,
                    reconnect_count=0,
                    error_count=0,
                    bytes_sent=0,
                    bytes_received=0
                )
            }
            
            # Test connection
            if await self._test_connection(exchange_name):
                self.connections[exchange_name]['metrics'].status = ConnectionStatus.CONNECTED
                self.logger.info(f"✅ Warm connection established: {exchange_name}")
                return True
            else:
                await self._close_connection(exchange_name)
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating warm connection to {exchange_name}: {e}")
            return False
            
    async def _test_connection(self, exchange_name: str) -> bool:
        """Test connection health"""
        try:
            connection = self.connections.get(exchange_name)
            if not connection:
                return False
                
            session = connection['session']
            api_config = connection['api_config']
            
            # Perform lightweight ping
            start_time = time.time()
            
            async with session.get(f"{api_config.get('base_url', '')}/api/v1/ping", 
                                 timeout=aiohttp.ClientTimeout(total=2.0)) as response:
                latency = (time.time() - start_time) * 1000
                
                connection['metrics'].last_ping = datetime.now()
                connection['metrics'].latency_ms = latency
                
                return response.status == 200
                
        except Exception as e:
            self.logger.warning(f"Connection test failed for {exchange_name}: {e}")
            return False
            
    async def _connection_monitor(self):
        """Monitor all connections and maintain health"""
        while self.is_running:
            try:
                for exchange_name, connection in list(self.connections.items()):
                    await self._monitor_connection(exchange_name, connection)
                    
                await asyncio.sleep(self.heartbeat_interval)
                
            except Exception as e:
                self.logger.error(f"Error in connection monitor: {e}")
                await asyncio.sleep(1)
                
    async def _monitor_connection(self, exchange_name: str, connection: Dict):
        """Monitor individual connection"""
        try:
            metrics = connection['metrics']
            now = datetime.now()
            
            # Check if connection is stale
            time_since_last_use = (now - connection['last_used']).total_seconds()
            time_since_last_ping = (now - metrics.last_ping).total_seconds()
            
            # Ping if needed
            if time_since_last_ping > 10:  # Ping every 10 seconds
                if await self._test_connection(exchange_name):
                    metrics.status = ConnectionStatus.CONNECTED
                else:
                    metrics.status = ConnectionStatus.ERROR
                    metrics.error_count += 1
                    
                    # Attempt reconnection
                    if metrics.error_count <= self.max_reconnect_attempts:
                        await self._reconnect_connection(exchange_name)
                    else:
                        self.logger.error(f"Max reconnect attempts reached for {exchange_name}")
                        
            # Close idle connections
            if time_since_last_use > self.warm_connection_timeout:
                await self._close_connection(exchange_name)
                
        except Exception as e:
            self.logger.error(f"Error monitoring connection {exchange_name}: {e}")
            
    async def _reconnect_connection(self, exchange_name: str):
        """Reconnect failed connection"""
        try:
            connection = self.connections.get(exchange_name)
            if not connection:
                return
                
            metrics = connection['metrics']
            metrics.status = ConnectionStatus.RECONNECTING
            metrics.reconnect_count += 1
            
            # Exponential backoff
            delay = self.reconnect_delay * (2 ** metrics.reconnect_count)
            await asyncio.sleep(min(delay, 5.0))  # Max 5 second delay
            
            # Close existing connection
            await self._close_connection(exchange_name)
            
            # Recreate connection
            api_config = connection['api_config']
            await self.create_warm_connection(exchange_name, api_config)
            
            self.logger.info(f"🔄 Reconnected: {exchange_name} (attempt {metrics.reconnect_count})")
            
        except Exception as e:
            self.logger.error(f"Error reconnecting {exchange_name}: {e}")
            
    async def _close_connection(self, exchange_name: str):
        """Close connection and cleanup"""
        try:
            connection = self.connections.get(exchange_name)
            if connection:
                await connection['session'].close()
                await connection['connector'].close()
                del self.connections[exchange_name]
                
        except Exception as e:
            self.logger.error(f"Error closing connection {exchange_name}: {e}")
            
    async def _heartbeat_maintenance(self):
        """Maintain heartbeat for all connections"""
        while self.is_running:
            try:
                # Update uptime metrics
                for exchange_name, connection in self.connections.items():
                    metrics = connection['metrics']
                    
                    # Calculate uptime
                    uptime = (datetime.now() - connection['created_at']).total_seconds()
                    total_time = uptime + (metrics.reconnect_count * 10)  # Estimate downtime
                    
                    metrics.uptime_percentage = (uptime / total_time) * 100 if total_time > 0 else 100
                    
                await asyncio.sleep(1.0)  # Update every second
                
            except Exception as e:
                self.logger.error(f"Error in heartbeat maintenance: {e}")
                await asyncio.sleep(5)
                
    async def execute_request(self, exchange_name: str, method: str, endpoint: str, 
                            data: Optional[Dict] = None, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute request with automatic connection management"""
        try:
            connection = self.connections.get(exchange_name)
            if not connection:
                raise ValueError(f"No connection to {exchange_name}")
                
            session = connection['session']
            connection['last_used'] = datetime.now()
            
            # Execute request
            start_time = time.time()
            
            if method.upper() == 'GET':
                async with session.get(endpoint, headers=headers) as response:
                    result = await response.json()
            elif method.upper() == 'POST':
                async with session.post(endpoint, json=data, headers=headers) as response:
                    result = await response.json()
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            # Update metrics
            execution_time = (time.time() - start_time) * 1000
            connection['metrics'].latency_ms = execution_time
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing request on {exchange_name}: {e}")
            raise
            
    async def get_connection_health(self) -> Dict[str, Any]:
        """Get overall connection health report"""
        try:
            total_connections = len(self.connections)
            healthy_connections = len([
                c for c in self.connections.values() 
                if c['metrics'].status == ConnectionStatus.CONNECTED
            ])
            
            avg_latency = 0
            if total_connections > 0:
                avg_latency = sum(c['metrics'].latency_ms for c in self.connections.values()) / total_connections
                
            return {
                'timestamp': datetime.now(),
                'total_connections': total_connections,
                'healthy_connections': healthy_connections,
                'health_percentage': (healthy_connections / total_connections) * 100 if total_connections > 0 else 0,
                'average_latency_ms': avg_latency,
                'connections': {
                    name: {
                        'status': conn['metrics'].status.value,
                        'latency_ms': conn['metrics'].latency_ms,
                        'uptime_percentage': conn['metrics'].uptime_percentage,
                        'reconnect_count': conn['metrics'].reconnect_count,
                        'error_count': conn['metrics'].error_count
                    }
                    for name, conn in self.connections.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting connection health: {e}")
            return {'error': str(e)}

class PerformanceOptimizer:
    """HP i5 PC performance optimization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cpu_cores = 4  # HP i5 typical cores
        self.optimization_settings = {
            'max_concurrent_tasks': 8,
            'memory_limit_mb': 4096,  # 4GB limit
            'cpu_affinity': [0, 1, 2, 3],  # Use all cores
            'process_priority': 'high'
        }
        
    async def initialize(self):
        """Initialize performance optimizations"""
        try:
            # Set process priority
            await self._set_process_priority()
            
            # Configure asyncio thread pool
            await self._configure_thread_pool()
            
            # Optimize memory usage
            await self._optimize_memory_usage()
            
            self.logger.info("⚡ Performance optimizer initialized for HP i5")
            
        except Exception as e:
            self.logger.error(f"Error initializing performance optimizer: {e}")
            
    async def _set_process_priority(self):
        """Set high priority for trading process"""
        try:
            # # import psutil  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            process = psutil.Process()
            
            # Set high priority (Windows: HIGH_PRIORITY_CLASS, Unix: nice value)
            if hasattr(process, 'nice'):
                process.nice(-10)  # Higher priority on Unix
            elif hasattr(process, 'set_nice'):
                process.set_nice(-10)
                
            self.logger.info("🚀 Process priority set to high")
            
        except Exception as e:
            self.logger.warning(f"Could not set process priority: {e}")
            
    async def _configure_thread_pool(self):
        """Configure asyncio thread pool for optimal performance"""
        try:
            # Set thread pool size based on CPU cores
            thread_pool_size = self.cpu_cores * 2
            
            # Configure default executor
            loop = asyncio.get_event_loop()
            loop.set_default_executor(
                asyncio.ThreadPoolExecutor(max_workers=thread_pool_size)
            )
            
            self.logger.info(f"🔧 Thread pool configured with {thread_pool_size} workers")
            
        except Exception as e:
            self.logger.warning(f"Could not configure thread pool: {e}")
            
    async def _optimize_memory_usage(self):
        """Optimize memory usage for trading operations"""
        try:
            # # import gc  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            # import sys  # Moved to function to avoid circular import
            
            # Force garbage collection
            gc.collect()
            
            # Set memory allocation strategy
            if hasattr(sys, 'setallocationstrategy'):
                sys.setallocationstrategy('debug')  # More conservative allocation
                
            self.logger.info("💾 Memory usage optimized")
            
        except Exception as e:
            self.logger.warning(f"Could not optimize memory: {e}")
            
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        try:
            # # import psutil  # Moved to function to avoid circular import  # Moved to function to avoid circular import
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Process-specific metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return {
                'timestamp': datetime.now(),
                'system_cpu_percent': cpu_percent,
                'system_memory_percent': memory_percent,
                'process_memory_mb': process_memory.rss / 1024 / 1024,
                'process_cpu_percent': process_cpu,
                'thread_count': process.num_threads(),
                'optimization_active': True
            }
            
        except Exception as e:
            self.logger.error(f"Error getting performance metrics: {e}")
            return {'error': str(e)}

class ZeroDowntimeManager:
    """Zero-downtime infrastructure manager"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connection_manager = AsyncConnectionManager()
        self.performance_optimizer = PerformanceOptimizer()
        self.is_running = False
        self.health_check_interval = 1.0  # 1 second health checks
        
    async def initialize(self):
        """Initialize zero-downtime infrastructure"""
        try:
            # Initialize components
            await self.connection_manager.initialize()
            await self.performance_optimizer.initialize()
            
            # Start health monitoring
            asyncio.create_task(self._health_monitor())
            
            # Start auto-healing
            asyncio.create_task(self._auto_healing_loop())
            
            self.is_running = True
            self.logger.info("🛡️ Zero-downtime infrastructure initialized")
            
        except Exception as e:
            self.logger.error(f"Error initializing zero-downtime manager: {e}")
            raise
            
    async def setup_exchange_connections(self, exchange_configs: Dict[str, Dict]):
        """Setup warm connections to all exchanges"""
        try:
            for exchange_name, config in exchange_configs.items():
                success = await self.connection_manager.create_warm_connection(
                    exchange_name, config
                )
                
                if success:
                    self.logger.info(f"✅ Warm connection ready: {exchange_name}")
                else:
                    self.logger.error(f"❌ Failed to connect: {exchange_name}")
                    
        except Exception as e:
            self.logger.error(f"Error setting up exchange connections: {e}")
            
    async def _health_monitor(self):
        """Monitor system health continuously"""
        while self.is_running:
            try:
                # Get connection health
                connection_health = await self.connection_manager.get_connection_health()
                
                # Get performance metrics
                performance_metrics = await self.performance_optimizer.get_performance_metrics()
                
                # Check for issues
                issues = []
                
                if connection_health.get('health_percentage', 100) < 80:
                    issues.append("Connection health below 80%")
                    
                if performance_metrics.get('system_memory_percent', 0) > 85:
                    issues.append("Memory usage above 85%")
                    
                if performance_metrics.get('system_cpu_percent', 0) > 90:
                    issues.append("CPU usage above 90%")
                    
                # Log issues
                if issues:
                    for issue in issues:
                        self.logger.warning(f"⚠️ Health issue: {issue}")
                        
                await asyncio.sleep(self.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                await asyncio.sleep(5)
                
    async def _auto_healing_loop(self):
        """Automatic healing of system issues"""
        while self.is_running:
            try:
                # Check for failed connections
                connection_health = await self.connection_manager.get_connection_health()
                
                for exchange_name, health in connection_health.get('connections', {}).items():
                    if health.get('status') == 'error':
                        self.logger.info(f"🔄 Auto-healing connection: {exchange_name}")
                        # Reconnection is handled automatically by connection manager
                        
                # Check performance issues
                performance_metrics = await self.performance_optimizer.get_performance_metrics()
                
                if performance_metrics.get('system_memory_percent', 0) > 90:
                    self.logger.info("🧹 Auto-cleaning memory")
                    # # import gc  # Moved to function to avoid circular import  # Moved to function to avoid circular # import gc  # Moved to function to avoid circular import.collect()
                    
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                self.logger.error(f"Error in auto-healing: {e}")
                await asyncio.sleep(10)
                
    async def execute_trade_request(self, exchange_name: str, request_data: Dict) -> Dict[str, Any]:
        """Execute trade request with zero-downtime guarantee"""
        try:
            # Ensure connection is healthy
            connection_health = await self.connection_manager.get_connection_health()
            
            if connection_health.get('health_percentage', 100) < 50:
                raise Exception("Connection health too low for trading")
                
            # Execute request
            result = await self.connection_manager.execute_request(
                exchange_name=exchange_name,
                method=request_data.get('method', 'POST'),
                endpoint=request_data.get('endpoint', ''),
                data=request_data.get('data'),
                headers=request_data.get('headers')
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing trade request: {e}")
            raise
            
    async def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            connection_health = await self.connection_manager.get_connection_health()
            performance_metrics = await self.performance_optimizer.get_performance_metrics()
            
            return {
                'timestamp': datetime.now(),
                'status': 'healthy' if self.is_running else 'unhealthy',
                'uptime_seconds': (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0)).total_seconds(),
                'connections': connection_health,
                'performance': performance_metrics,
                'zero_downtime_active': self.is_running
            }
            
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}
            
    async def shutdown(self):
        """Graceful shutdown"""
        try:
            self.is_running = False
            
            # Close all connections
            for exchange_name in list(self.connection_manager.connections.keys()):
                await self.connection_manager._close_connection(exchange_name)
                
            self.logger.info("🛑 Zero-downtime manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

# Global zero-downtime manager
zero_downtime_manager = ZeroDowntimeManager()
