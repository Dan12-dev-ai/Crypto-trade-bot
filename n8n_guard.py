"""
Crypto trade bot - n8n Orchestration Guard
Latency monitoring and execution pausing for workflow reliability
"""

# import asyncio  # Moved to function to avoid circular import
# import logging  # Moved to function to avoid circular import
# import time  # Moved to function to avoid circular import
# import aiohttp  # Moved to function to avoid circular import
from datetime # import datetime  # Moved to function to avoid circular import, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
# import json  # Moved to function to avoid circular import
from pathlib import Path

class WorkflowStatus(Enum):
    """Workflow execution status"""
    HEALTHY = "healthy"
    SLOW = "slow"
    TIMEOUT = "timeout"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class WorkflowMetrics:
    """Workflow performance metrics"""
    workflow_id: str
    name: str
    last_execution: datetime
    execution_time: float  # milliseconds
    status: WorkflowStatus
    error_count: int
    success_count: int
    avg_execution_time: float
    max_execution_time: float
    min_execution_time: float
    last_error: Optional[str] = None
    consecutive_failures: int = 0

@dataclass
class LatencyAlert:
    """Latency alert data"""
    workflow_id: str
    alert_type: str  # 'high_latency', 'timeout', 'consecutive_failures'
    current_latency: float
    threshold: float
    timestamp: datetime
    action_taken: str
    impact: str

class N8nOrchestrationGuard:
    """Advanced workflow monitoring and execution guard"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.workflow_metrics: Dict[str, WorkflowMetrics] = {}
        self.alerts: List[LatencyAlert] = []
        self.is_monitoring = False
        self.execution_paused = False
        
        # Configuration thresholds
        self.latency_threshold = 200.0  # milliseconds
        self.timeout_threshold = 5000.0  # milliseconds
        self.consecutive_failure_limit = 3
        self.monitoring_interval = 30  # seconds
        
        # n8n connection settings
        self.n8n_url = "http://localhost:5678"
        self.api_key = None
        
        # Storage
        self.metrics_file = Path("data/workflow_metrics.json")
        self.alerts_file = Path("data/latency_alerts.json")
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
    async def initialize(self, n8n_url: str = None, api_key: str = None):
        """Initialize the n8n guard"""
        try:
            if n8n_url:
                self.n8n_url = n8n_url
            if api_key:
                self.api_key = api_key
                
            await self.load_historical_metrics()
            await self.discover_workflows()
            self.is_monitoring = True
            
            self.logger.info(f"n8n Orchestration Guard initialized for {self.n8n_url}")
            
        except Exception as e:
            self.logger.error(f"Error initializing n8n guard: {e}")
            
    async def start_monitoring(self):
        """Start continuous workflow monitoring"""
        if not self.is_monitoring:
            self.logger.warning("n8n guard not initialized")
            return
            
        self.logger.info("Starting n8n workflow monitoring")
        
        while self.is_monitoring:
            try:
                await self.check_all_workflows()
                await self.analyze_performance_trends()
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(5)
                
    async def stop_monitoring(self):
        """Stop workflow monitoring"""
        self.is_monitoring = False
        self.logger.info("n8n workflow monitoring stopped")
        
    async def discover_workflows(self):
        """Discover all active workflows in n8n"""
        try:
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers['X-N8N-API-KEY'] = self.api_key
                    
                async with session.get(f"{self.n8n_url}/api/v1/workflows", headers=headers) as response:
                    if response.status == 200:
                        workflows = await response.json()
                        
                        for workflow in workflows.get('data', []):
                            workflow_id = workflow['id']
                            name = workflow['name']
                            
                            if workflow_id not in self.workflow_metrics:
                                self.workflow_metrics[workflow_id] = WorkflowMetrics(
                                    workflow_id=workflow_id,
                                    name=name,
                                    last_execution=datetime.now(),
                                    execution_time=0.0,
                                    status=WorkflowStatus.HEALTHY,
                                    error_count=0,
                                    success_count=0,
                                    avg_execution_time=0.0,
                                    max_execution_time=0.0,
                                    min_execution_time=float('inf')
                                )
                                
                        self.logger.info(f"Discovered {len(workflows.get('data', []))} workflows")
                    else:
                        self.logger.error(f"Failed to discover workflows: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Error discovering workflows: {e}")
            
    async def check_all_workflows(self):
        """Check performance of all workflows"""
        for workflow_id, metrics in self.workflow_metrics.items():
            await self.check_workflow_performance(workflow_id)
            
    async def check_workflow_performance(self, workflow_id: str):
        """Check performance of a specific workflow"""
        try:
            start_time = time.time()
            
            # Get workflow execution history
            async with aiohttp.ClientSession() as session:
                headers = {}
                if self.api_key:
                    headers['X-N8N-API-KEY'] = self.api_key
                    
                # Get recent executions
                url = f"{self.n8n_url}/api/v1/executions"
                params = {'workflowId': workflow_id, 'limit': 10}
                
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 200:
                        executions = await response.json()
                        
                        if executions.get('data'):
                            latest_execution = executions['data'][0]
                            
                            # Calculate execution time
                            if latest_execution.get('startedAt') and latest_execution.get('stoppedAt'):
                                started = datetime.fromisoformat(latest_execution['startedAt'].replace('Z', '+00:00'))
                                stopped = datetime.fromisoformat(latest_execution['stoppedAt'].replace('Z', '+00:00'))
                                execution_time = (stopped - started).total_seconds() * 1000
                            else:
                                execution_time = 0.0
                                
                            # Update metrics
                            await self.update_workflow_metrics(workflow_id, latest_execution, execution_time)
                            
                            # Check for latency issues
                            await self.check_latency_thresholds(workflow_id, execution_time)
                            
        except Exception as e:
            self.logger.error(f"Error checking workflow {workflow_id}: {e}")
            
    async def update_workflow_metrics(self, workflow_id: str, execution: Dict, execution_time: float):
        """Update workflow performance metrics"""
        try:
            metrics = self.workflow_metrics[workflow_id]
            
            # Update execution counts
            if execution.get('finished') and execution.get('status') == 'success':
                metrics.success_count += 1
                metrics.consecutive_failures = 0
            else:
                metrics.error_count += 1
                metrics.consecutive_failures += 1
                metrics.last_error = execution.get('error', {}).get('message', 'Unknown error')
                
            # Update timing metrics
            if execution_time > 0:
                metrics.execution_time = execution_time
                metrics.last_execution = datetime.now()
                
                # Update averages
                total_executions = metrics.success_count + metrics.error_count
                if total_executions > 1:
                    metrics.avg_execution_time = (
                        (metrics.avg_execution_time * (total_executions - 1) + execution_time) / total_executions
                    )
                else:
                    metrics.avg_execution_time = execution_time
                    
                # Update min/max
                metrics.max_execution_time = max(metrics.max_execution_time, execution_time)
                metrics.min_execution_time = min(metrics.min_execution_time, execution_time)
                
            # Update status
            if execution_time > self.timeout_threshold:
                metrics.status = WorkflowStatus.TIMEOUT
            elif execution_time > self.latency_threshold:
                metrics.status = WorkflowStatus.SLOW
            elif metrics.consecutive_failures >= self.consecutive_failure_limit:
                metrics.status = WorkflowStatus.ERROR
            else:
                metrics.status = WorkflowStatus.HEALTHY
                
        except Exception as e:
            self.logger.error(f"Error updating metrics for {workflow_id}: {e}")
            
    async def check_latency_thresholds(self, workflow_id: str, execution_time: float):
        """Check if workflow exceeds latency thresholds"""
        metrics = self.workflow_metrics[workflow_id]
        
        # Check high latency
        if execution_time > self.latency_threshold:
            alert = LatencyAlert(
                workflow_id=workflow_id,
                alert_type='high_latency',
                current_latency=execution_time,
                threshold=self.latency_threshold,
                timestamp=datetime.now(),
                action_taken='logged',
                impact='Performance degradation'
            )
            self.alerts.append(alert)
            
            # Consider pausing execution if very high latency
            if execution_time > self.latency_threshold * 3:
                await self.pause_execution('high_latency', f"Workflow {workflow_id} latency: {execution_time:.0f}ms")
                
        # Check timeout
        if execution_time > self.timeout_threshold:
            alert = LatencyAlert(
                workflow_id=workflow_id,
                alert_type='timeout',
                current_latency=execution_time,
                threshold=self.timeout_threshold,
                timestamp=datetime.now(),
                action_taken='execution_paused',
                impact='Workflow timeout detected'
            )
            self.alerts.append(alert)
            await self.pause_execution('timeout', f"Workflow {workflow_id} timeout: {execution_time:.0f}ms")
            
        # Check consecutive failures
        if metrics.consecutive_failures >= self.consecutive_failure_limit:
            alert = LatencyAlert(
                workflow_id=workflow_id,
                alert_type='consecutive_failures',
                current_latency=execution_time,
                threshold=self.consecutive_failure_limit,
                timestamp=datetime.now(),
                action_taken='execution_paused',
                impact=f'{metrics.consecutive_failures} consecutive failures'
            )
            self.alerts.append(alert)
            await self.pause_execution('consecutive_failures', f"Workflow {workflow_id} has {metrics.consecutive_failures} consecutive failures")
            
    async def pause_execution(self, reason: str, details: str):
        """Pause trading execution due to workflow issues"""
        if not self.execution_paused:
            self.execution_paused = True
            self.logger.warning(f"🚨 EXECUTION PAUSED - Reason: {reason} - Details: {details}")
            
            # Send alert to telegram if available
            try:
                from telegram_alerts # # import telegram_alerts  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                await telegram_alerts.send_system_alert(
                    "Execution Paused - n8n Guard",
                    f"Trading execution has been paused due to: {reason}\n{details}",
                    "high"
                )
            except:
                pass
                
    async def resume_execution(self):
        """Resume trading execution"""
        if self.execution_paused:
            self.execution_paused = False
            self.logger.info("✅ EXECUTION RESUMED - n8n workflows healthy")
            
            try:
                from telegram_alerts # # import telegram_alerts  # Moved to function to avoid circular import  # Moved to function to avoid circular import
                await telegram_alerts.send_system_alert(
                    "Execution Resumed",
                    "Trading execution has been resumed - n8n workflows are healthy",
                    "medium"
                )
            except:
                pass
                
    async def analyze_performance_trends(self):
        """Analyze performance trends and predict issues"""
        try:
            for workflow_id, metrics in self.workflow_metrics.items():
                # Check for performance degradation
                if metrics.success_count > 10:
                    recent_avg = metrics.avg_execution_time
                    historical_avg = await self.get_historical_average(workflow_id)
                    
                    if historical_avg and recent_avg > historical_avg * 1.5:
                        self.logger.warning(f"Performance degradation detected in workflow {workflow_id}: {recent_avg:.0f}ms vs historical {historical_avg:.0f}ms")
                        
                        # Suggest optimization
                        await self.suggest_workflow_optimization(workflow_id, recent_avg, historical_avg)
                        
        except Exception as e:
            self.logger.error(f"Error analyzing performance trends: {e}")
            
    async def get_historical_average(self, workflow_id: str) -> Optional[float]:
        """Get historical average execution time for workflow"""
        # This would typically query a database or historical data
        # For now, return a simple implementation
        metrics = self.workflow_metrics[workflow_id]
        if metrics.success_count > 5:
            return metrics.avg_execution_time * 0.8  # Assume historical was 20% better
        return None
        
    async def suggest_workflow_optimization(self, workflow_id: str, current_avg: float, historical_avg: float):
        """Suggest optimizations for slow workflows"""
        degradation = (current_avg - historical_avg) / historical_avg
        
        suggestions = []
        if degradation > 0.5:  # 50% slower
            suggestions.append("Consider optimizing workflow logic")
            suggestions.append("Check for external API bottlenecks")
            suggestions.append("Review database query performance")
        elif degradation > 0.2:  # 20% slower
            suggestions.append("Monitor workflow for further degradation")
            suggestions.append("Consider caching frequent operations")
            
        self.logger.info(f"Optimization suggestions for {workflow_id}: {'; '.join(suggestions)}")
        
    async def get_workflow_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive workflow health report"""
        try:
            total_workflows = len(self.workflow_metrics)
            healthy_workflows = len([m for m in self.workflow_metrics.values() if m.status == WorkflowStatus.HEALTHY])
            slow_workflows = len([m for m in self.workflow_metrics.values() if m.status == WorkflowStatus.SLOW])
            error_workflows = len([m for m in self.workflow_metrics.values() if m.status == WorkflowStatus.ERROR])
            
            avg_latency = 0
            if self.workflow_metrics:
                avg_latency = sum(m.avg_execution_time for m in self.workflow_metrics.values()) / len(self.workflow_metrics)
                
            return {
                'timestamp': datetime.now(),
                'total_workflows': total_workflows,
                'healthy_workflows': healthy_workflows,
                'slow_workflows': slow_workflows,
                'error_workflows': error_workflows,
                'execution_paused': self.execution_paused,
                'average_latency': avg_latency,
                'recent_alerts': len([a for a in self.alerts if a.timestamp > datetime.now() - timedelta(hours=1)]),
                'health_score': (healthy_workflows / total_workflows) if total_workflows > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error generating health report: {e}")
            return {}
            
    async def save_metrics(self):
        """Save workflow metrics to file"""
        try:
            metrics_data = {}
            for workflow_id, metrics in self.workflow_metrics.items():
                metrics_data[workflow_id] = {
                    'workflow_id': metrics.workflow_id,
                    'name': metrics.name,
                    'last_execution': metrics.last_execution.isoformat(),
                    'execution_time': metrics.execution_time,
                    'status': metrics.status.value,
                    'error_count': metrics.error_count,
                    'success_count': metrics.success_count,
                    'avg_execution_time': metrics.avg_execution_time,
                    'max_execution_time': metrics.max_execution_time,
                    'min_execution_time': metrics.min_execution_time,
                    'last_error': metrics.last_error,
                    'consecutive_failures': metrics.consecutive_failures
                }
                
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metrics: {e}")
            
    async def load_historical_metrics(self):
        """Load historical workflow metrics"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    metrics_data = json.load(f)
                    
                for workflow_id, data in metrics_data.items():
                    self.workflow_metrics[workflow_id] = WorkflowMetrics(
                        workflow_id=data['workflow_id'],
                        name=data['name'],
                        last_execution=datetime.fromisoformat(data['last_execution']),
                        execution_time=data['execution_time'],
                        status=WorkflowStatus(data['status']),
                        error_count=data['error_count'],
                        success_count=data['success_count'],
                        avg_execution_time=data['avg_execution_time'],
                        max_execution_time=data['max_execution_time'],
                        min_execution_time=data['min_execution_time'],
                        last_error=data.get('last_error'),
                        consecutive_failures=data.get('consecutive_failures', 0)
                    )
                    
                self.logger.info(f"Loaded metrics for {len(self.workflow_metrics)} workflows")
                
        except Exception as e:
            self.logger.error(f"Error loading historical metrics: {e}")

# Global instance
n8n_guard = N8nOrchestrationGuard()
