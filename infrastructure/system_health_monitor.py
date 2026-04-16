"""
UOTA Elite v2 - System Health Monitor
Monitors system stability without touching trading logic
"""

# import asyncio  # Moved to function to avoid circular import
# import psutil  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import json  # Moved to function to avoid circular import
# import os  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
# import aiofiles  # Moved to function to avoid circular import
# import aiohttp  # Moved to function to avoid circular import

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_latency: float
    mt5_connection_status: bool
    active_processes: int
    system_load: float
    available_memory_gb: float

@dataclass
class HealthAlert:
    """Health alert information"""
    timestamp: datetime
    level: AlertLevel
    component: str
    message: str
    metric_value: Optional[float]
    threshold: Optional[float]
    action_required: str

class SystemHealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.is_monitoring = False
        self.metrics_history = []
        self.alerts = []
        self.health_status = HealthStatus.UNKNOWN
        
        # Health thresholds (configurable)
        self.thresholds = {
            'cpu_warning': 70.0,      # % CPU usage
            'cpu_critical': 90.0,     # % CPU usage
            'memory_warning': 75.0,    # % Memory usage
            'memory_critical': 90.0,   # % Memory usage
            'disk_warning': 80.0,      # % Disk usage
            'disk_critical': 95.0,     # % Disk usage
            'latency_warning': 200.0,  # ms
            'latency_critical': 500.0, # ms
            'load_warning': 2.0,       # System load average
            'load_critical': 4.0,      # System load average
            'min_memory_gb': 1.0       # Minimum available memory
        }
        
        # Monitoring intervals
        self.monitor_interval = 30  # seconds
        self.max_history_size = 1000  # metrics to keep
        
        # External services to monitor
        self.external_services = {
            'mt5_connection': False,
            'network_connectivity': False
        }
        
    async def start_monitoring(self):
        """Start continuous health monitoring"""
        try:
            self.is_monitoring = True
            self.logger.info("🏥 Starting System Health Monitor...")
            
            while self.is_monitoring:
                try:
                    # Collect metrics
                    metrics = await self._collect_metrics()
                    self.metrics_history.append(metrics)
                    
                    # Clean old metrics
                    if len(self.metrics_history) > self.max_history_size:
                        self.metrics_history = self.metrics_history[-self.max_history_size:]
                    
                    # Evaluate health
                    await self._evaluate_health(metrics)
                    
                    # Check external services
                    await self._check_external_services()
                    
                    # Save metrics
                    await self._save_metrics(metrics)
                    
                    await asyncio.sleep(self.monitor_interval)
                    
                except Exception as e:
                    self.logger.error(f"❌ Error in health monitoring loop: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            self.logger.error(f"❌ Critical error in health monitor: {e}")
            self.is_monitoring = False
    
    async def _collect_metrics(self) -> SystemMetrics:
        """Collect system performance metrics"""
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            system_load = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_memory_gb = memory.available / (1024**3)
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network latency
            network_latency = await self._measure_network_latency()
            
            # Process count
            active_processes = len(psutil.pids())
            
            # MT5 connection status
            mt5_status = await self._check_mt5_connection()
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_percent=disk_percent,
                network_latency=network_latency,
                mt5_connection_status=mt5_status,
                active_processes=active_processes,
                system_load=system_load,
                available_memory_gb=available_memory_gb
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error collecting metrics: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                disk_percent=0.0,
                network_latency=999.0,
                mt5_connection_status=False,
                active_processes=0,
                system_load=0.0,
                available_memory_gb=0.0
            )
    
    async def _measure_network_latency(self) -> float:
        """Measure network latency to reliable endpoint"""
        try:
            # import time  # Moved to function to avoid circular import
            start_time = time.time()
            
            # Test connectivity to Google DNS
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get('https://8.8.8.8') as response:
                    latency = (time.time() - start_time) * 1000  # Convert to ms
                    return min(latency, 999.0)  # Cap at 999ms
                    
        except Exception as e:
            self.logger.debug(f"Network latency measurement failed: {e}")
            return 999.0
    
    async def _check_mt5_connection(self) -> bool:
        """Check MT5 connection status"""
        try:
            from mt5_integration # import mt5_integration  # Moved to function to avoid circular import
            return mt5_integration.is_connected
        except Exception:
            return False
    
    async def _check_external_services(self):
        """Check status of external services"""
        try:
            # Network connectivity
            self.external_services['network_connectivity'] = await self._test_network_connectivity()
            
            # MT5 connection
            self.external_services['mt5_connection'] = await self._check_mt5_connection()
            
        except Exception as e:
            self.logger.error(f"❌ Error checking external services: {e}")
    
    async def _test_network_connectivity(self) -> bool:
        """Test basic network connectivity"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get('https://httpbin.org/status/200') as response:
                    return response.status == 200
        except:
            return False
    
    async def _evaluate_health(self, metrics: SystemMetrics):
        """Evaluate system health based on metrics"""
        try:
            alerts = []
            
            # CPU checks
            if metrics.cpu_percent >= self.thresholds['cpu_critical']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.CRITICAL,
                    component="CPU",
                    message=f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
                    metric_value=metrics.cpu_percent,
                    threshold=self.thresholds['cpu_critical'],
                    action_required="Reduce system load or scale resources"
                ))
            elif metrics.cpu_percent >= self.thresholds['cpu_warning']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.WARNING,
                    component="CPU",
                    message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                    metric_value=metrics.cpu_percent,
                    threshold=self.thresholds['cpu_warning'],
                    action_required="Monitor CPU usage"
                ))
            
            # Memory checks
            if metrics.memory_percent >= self.thresholds['memory_critical']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.CRITICAL,
                    component="Memory",
                    message=f"Critical memory usage: {metrics.memory_percent:.1f}%",
                    metric_value=metrics.memory_percent,
                    threshold=self.thresholds['memory_critical'],
                    action_required="Free memory or restart system"
                ))
            elif metrics.memory_percent >= self.thresholds['memory_warning']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.WARNING,
                    component="Memory",
                    message=f"High memory usage: {metrics.memory_percent:.1f}%",
                    metric_value=metrics.memory_percent,
                    threshold=self.thresholds['memory_warning'],
                    action_required="Monitor memory usage"
                ))
            
            # Available memory check
            if metrics.available_memory_gb < self.thresholds['min_memory_gb']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.CRITICAL,
                    component="Memory",
                    message=f"Low available memory: {metrics.available_memory_gb:.1f}GB",
                    metric_value=metrics.available_memory_gb,
                    threshold=self.thresholds['min_memory_gb'],
                    action_required="Free memory immediately"
                ))
            
            # Disk checks
            if metrics.disk_percent >= self.thresholds['disk_critical']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.CRITICAL,
                    component="Disk",
                    message=f"Critical disk usage: {metrics.disk_percent:.1f}%",
                    metric_value=metrics.disk_percent,
                    threshold=self.thresholds['disk_critical'],
                    action_required="Clean disk space immediately"
                ))
            elif metrics.disk_percent >= self.thresholds['disk_warning']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.WARNING,
                    component="Disk",
                    message=f"High disk usage: {metrics.disk_percent:.1f}%",
                    metric_value=metrics.disk_percent,
                    threshold=self.thresholds['disk_warning'],
                    action_required="Monitor disk usage"
                ))
            
            # Network latency checks
            if metrics.network_latency >= self.thresholds['latency_critical']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.CRITICAL,
                    component="Network",
                    message=f"Critical network latency: {metrics.network_latency:.1f}ms",
                    metric_value=metrics.network_latency,
                    threshold=self.thresholds['latency_critical'],
                    action_required="Check network connection"
                ))
            elif metrics.network_latency >= self.thresholds['latency_warning']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.WARNING,
                    component="Network",
                    message=f"High network latency: {metrics.network_latency:.1f}ms",
                    metric_value=metrics.network_latency,
                    threshold=self.thresholds['latency_warning'],
                    action_required="Monitor network performance"
                ))
            
            # System load checks
            if metrics.system_load >= self.thresholds['load_critical']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.CRITICAL,
                    component="System",
                    message=f"Critical system load: {metrics.system_load:.1f}",
                    metric_value=metrics.system_load,
                    threshold=self.thresholds['load_critical'],
                    action_required="Reduce system load"
                ))
            elif metrics.system_load >= self.thresholds['load_warning']:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.WARNING,
                    component="System",
                    message=f"High system load: {metrics.system_load:.1f}",
                    metric_value=metrics.system_load,
                    threshold=self.thresholds['load_warning'],
                    action_required="Monitor system load"
                ))
            
            # MT5 connection check
            if not metrics.mt5_connection_status:
                alerts.append(HealthAlert(
                    timestamp=metrics.timestamp,
                    level=AlertLevel.CRITICAL,
                    component="MT5",
                    message="MT5 connection lost",
                    metric_value=None,
                    threshold=None,
                    action_required="Reconnect MT5 immediately"
                ))
            
            # Add alerts to list
            self.alerts.extend(alerts)
            
            # Keep only recent alerts (last 100)
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            # Determine overall health status
            critical_alerts = [a for a in alerts if a.level == AlertLevel.CRITICAL]
            warning_alerts = [a for a in alerts if a.level == AlertLevel.WARNING]
            
            if critical_alerts:
                self.health_status = HealthStatus.CRITICAL
            elif warning_alerts:
                self.health_status = HealthStatus.WARNING
            else:
                self.health_status = HealthStatus.HEALTHY
            
            # Log alerts
            for alert in alerts:
                if alert.level == AlertLevel.CRITICAL:
                    self.logger.critical(f"🚨 {alert.component}: {alert.message}")
                elif alert.level == AlertLevel.WARNING:
                    self.logger.warning(f"⚠️ {alert.component}: {alert.message}")
            
            # Handle critical alerts
            if critical_alerts:
                await self._handle_critical_alerts(critical_alerts)
                
        except Exception as e:
            self.logger.error(f"❌ Error evaluating health: {e}")
    
    async def _handle_critical_alerts(self, critical_alerts: List[HealthAlert]):
        """Handle critical health alerts"""
        try:
            # Check if trading should be paused
            pause_trading = False
            pause_reasons = []
            
            for alert in critical_alerts:
                if alert.component in ["CPU", "Memory", "Disk"]:
                    pause_trading = True
                    pause_reasons.append(f"{alert.component} critical: {alert.message}")
                elif alert.component == "MT5":
                    pause_trading = True
                    pause_reasons.append("MT5 connection lost")
            
            if pause_trading:
                self.logger.critical("🚨 CRITICAL: Pausing trading due to system issues")
                self.logger.critical(f"🎯 Reasons: {'; '.join(pause_reasons)}")
                
                # This would integrate with trading system to pause
                # For now, just log the critical alert
                
        except Exception as e:
            self.logger.error(f"❌ Error handling critical alerts: {e}")
    
    async def _save_metrics(self, metrics: SystemMetrics):
        """Save metrics to file"""
        try:
            os.makedirs('logs/health', exist_ok=True)
            
            log_file = f"logs/health/health_metrics_{datetime.now().strftime('%Y-%m-%d')}.json"
            
            # Read existing metrics
            existing_metrics = []
            if os.path.exists(log_file):
                async with aiofiles.open(log_file, 'r') as f:
                    content = await f.read()
                    if content:
                        existing_metrics = json.loads(content)
            
            # Add new metrics
            metrics_dict = asdict(metrics)
            metrics_dict['timestamp'] = metrics.timestamp.isoformat()
            existing_metrics.append(metrics_dict)
            
            # Keep only last 24 hours of data
            cutoff_time = (datetime.now() - timedelta(hours=24)).isoformat()
            existing_metrics = [m for m in existing_metrics if m['timestamp'] > cutoff_time]
            
            # Save metrics
            async with aiofiles.open(log_file, 'w') as f:
                await f.write(json.dumps(existing_metrics, indent=2))
                
        except Exception as e:
            self.logger.error(f"❌ Error saving metrics: {e}")
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        try:
            latest_metrics = self.metrics_history[-1] if self.metrics_history else None
            
            return {
                'health_status': self.health_status.value,
                'monitoring_active': self.is_monitoring,
                'latest_metrics': asdict(latest_metrics) if latest_metrics else None,
                'external_services': self.external_services,
                'recent_alerts': [
                    {
                        'timestamp': a.timestamp.isoformat(),
                        'level': a.level.value,
                        'component': a.component,
                        'message': a.message,
                        'action_required': a.action_required
                    }
                    for a in self.alerts[-10:]  # Last 10 alerts
                ],
                'metrics_count': len(self.metrics_history),
                'alerts_count': len(self.alerts),
                'thresholds': self.thresholds,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting current status: {e}")
            return {'error': str(e)}
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get health summary for dashboard"""
        try:
            if not self.metrics_history:
                return {'status': 'no_data', 'message': 'No metrics available'}
            
            # Calculate averages for last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_metrics = [m for m in self.metrics_history if m.timestamp > one_hour_ago]
            
            if not recent_metrics:
                return {'status': 'no_recent_data', 'message': 'No recent metrics available'}
            
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            avg_latency = sum(m.network_latency for m in recent_metrics) / len(recent_metrics)
            
            return {
                'status': self.health_status.value,
                'period_hours': 1,
                'metrics_count': len(recent_metrics),
                'averages': {
                    'cpu_percent': avg_cpu,
                    'memory_percent': avg_memory,
                    'network_latency_ms': avg_latency
                },
                'external_services': self.external_services,
                'critical_alerts': len([a for a in self.alerts if a.level == AlertLevel.CRITICAL]),
                'warning_alerts': len([a for a in self.alerts if a.level == AlertLevel.WARNING]),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Error getting health summary: {e}")
            return {'error': str(e)}
    
    def stop_monitoring(self):
        """Stop health monitoring"""
        self.is_monitoring = False
        self.logger.info("🏥 System Health Monitor stopped")

# Global health monitor instance
system_health_monitor = SystemHealthMonitor()
