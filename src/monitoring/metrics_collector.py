"""
Metrics collection and monitoring system.

This module provides comprehensive metrics collection for monitoring
application performance, health, and business metrics.
"""

import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import psutil
import json

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Represents a single metric measurement."""
    name: str
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class Alert:
    """Represents an alert condition."""
    name: str
    condition: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    severity: str  # 'critical', 'warning', 'info'
    description: str = ""
    enabled: bool = True


class MetricsCollector:
    """
    Comprehensive metrics collection system.
    
    Collects application, system, and business metrics with
    configurable collection intervals and retention policies.
    """
    
    def __init__(self, retention_hours: int = 24, collection_interval: int = 15):
        """
        Initialize metrics collector.
        
        Args:
            retention_hours: How long to keep metrics in memory
            collection_interval: Collection interval in seconds
        """
        self.retention_hours = retention_hours
        self.collection_interval = collection_interval
        
        # Metrics storage
        self.metrics = defaultdict(lambda: deque(maxlen=retention_hours * 240))  # 240 = 3600/15
        self.counters = defaultdict(float)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        
        # Alerts
        self.alerts = {}
        self.alert_history = deque(maxlen=1000)
        self.alert_callbacks = []
        
        # Collection state
        self._collecting = False
        self._collection_thread = None
        self._lock = threading.RLock()
        
        # Custom collectors
        self.custom_collectors = []
        
        logger.info(f"MetricsCollector initialized with {retention_hours}h retention, {collection_interval}s interval")
    
    def start_collection(self):
        """Start automatic metrics collection."""
        if self._collecting:
            logger.warning("Metrics collection already started")
            return
        
        self._collecting = True
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        
        logger.info("Metrics collection started")
    
    def stop_collection(self):
        """Stop automatic metrics collection."""
        self._collecting = False
        
        if self._collection_thread:
            self._collection_thread.join(timeout=5)
        
        logger.info("Metrics collection stopped")
    
    def _collection_loop(self):
        """Main collection loop."""
        while self._collecting:
            try:
                self._collect_system_metrics()
                self._collect_application_metrics()
                self._run_custom_collectors()
                self._check_alerts()
                self._cleanup_old_metrics()
                
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
            
            time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            process = psutil.Process()
            
            # CPU metrics
            self.record_gauge("system.cpu.percent", process.cpu_percent())
            self.record_gauge("system.cpu.count", psutil.cpu_count())
            
            # Memory metrics
            memory_info = process.memory_info()
            self.record_gauge("system.memory.rss_mb", memory_info.rss / 1024 / 1024)
            self.record_gauge("system.memory.vms_mb", memory_info.vms / 1024 / 1024)
            self.record_gauge("system.memory.percent", process.memory_percent())
            
            # System memory
            sys_memory = psutil.virtual_memory()
            self.record_gauge("system.memory.total_gb", sys_memory.total / 1024 / 1024 / 1024)
            self.record_gauge("system.memory.available_gb", sys_memory.available / 1024 / 1024 / 1024)
            self.record_gauge("system.memory.used_percent", sys_memory.percent)
            
            # Thread and file descriptor counts
            self.record_gauge("system.threads", process.num_threads())
            if hasattr(process, 'num_fds'):
                self.record_gauge("system.file_descriptors", process.num_fds())
            
            # Network connections
            connections = process.connections()
            self.record_gauge("system.connections.total", len(connections))
            self.record_gauge("system.connections.established", 
                            len([c for c in connections if c.status == 'ESTABLISHED']))
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")
    
    def _collect_application_metrics(self):
        """Collect application-specific metrics."""
        try:
            # Application uptime
            uptime_seconds = time.time() - getattr(self, '_start_time', time.time())
            self.record_gauge("app.uptime_seconds", uptime_seconds)
            
            # Thread pool metrics (if available)
            try:
                from src.optimization.performance_optimizer import performance_optimizer
                stats = performance_optimizer.get_performance_stats()
                
                # Cache metrics
                cache_stats = stats.get('cache', {})
                self.record_gauge("app.cache.hits", cache_stats.get('hits', 0))
                self.record_gauge("app.cache.misses", cache_stats.get('misses', 0))
                self.record_gauge("app.cache.hit_rate", cache_stats.get('hit_rate', 0))
                
                # Request metrics
                request_stats = stats.get('requests', {})
                self.record_counter("app.requests.total", request_stats.get('total_count', 0))
                self.record_counter("app.requests.errors", request_stats.get('error_count', 0))
                self.record_gauge("app.requests.avg_response_time", request_stats.get('avg_response_time', 0))
                
            except ImportError:
                pass  # Optimization module not available
            
        except Exception as e:
            logger.warning(f"Failed to collect application metrics: {e}")
    
    def _run_custom_collectors(self):
        """Run custom metric collectors."""
        for collector in self.custom_collectors:
            try:
                collector(self)
            except Exception as e:
                logger.warning(f"Custom collector failed: {e}")
    
    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Record a counter metric (cumulative)."""
        with self._lock:
            self.counters[name] += value
            self._record_metric(name, self.counters[name], labels or {})
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a gauge metric (point-in-time value)."""
        with self._lock:
            self.gauges[name] = value
            self._record_metric(name, value, labels or {})
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram metric (distribution of values)."""
        with self._lock:
            self.histograms[name].append(value)
            # Keep only recent values
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            
            self._record_metric(name, value, labels or {})
    
    def _record_metric(self, name: str, value: float, labels: Dict[str, str]):
        """Internal method to record a metric."""
        metric = Metric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            labels=labels
        )
        
        self.metrics[name].append(metric)
    
    def get_metric_value(self, name: str) -> Optional[float]:
        """Get the latest value for a metric."""
        with self._lock:
            if name in self.metrics and self.metrics[name]:
                return self.metrics[name][-1].value
            return None
    
    def get_metric_history(self, name: str, duration_minutes: int = 60) -> List[Metric]:
        """Get metric history for the specified duration."""
        with self._lock:
            if name not in self.metrics:
                return []
            
            cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
            return [m for m in self.metrics[name] if m.timestamp > cutoff_time]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metric values."""
        with self._lock:
            result = {}
            
            for name, metric_list in self.metrics.items():
                if metric_list:
                    latest = metric_list[-1]
                    result[name] = {
                        'value': latest.value,
                        'timestamp': latest.timestamp.isoformat(),
                        'labels': latest.labels
                    }
            
            return result
    
    def add_alert(self, alert: Alert):
        """Add an alert condition."""
        self.alerts[alert.name] = alert
        logger.info(f"Alert added: {alert.name}")
    
    def remove_alert(self, name: str):
        """Remove an alert condition."""
        if name in self.alerts:
            del self.alerts[name]
            logger.info(f"Alert removed: {name}")
    
    def add_alert_callback(self, callback: Callable):
        """Add a callback for alert notifications."""
        self.alert_callbacks.append(callback)
    
    def _check_alerts(self):
        """Check all alert conditions."""
        for alert_name, alert in self.alerts.items():
            if not alert.enabled:
                continue
            
            try:
                current_value = self.get_metric_value(alert.condition)
                if current_value is None:
                    continue
                
                triggered = self._evaluate_alert_condition(current_value, alert)
                
                if triggered:
                    self._trigger_alert(alert, current_value)
                    
            except Exception as e:
                logger.error(f"Error checking alert {alert_name}: {e}")
    
    def _evaluate_alert_condition(self, value: float, alert: Alert) -> bool:
        """Evaluate if an alert condition is met."""
        operators = {
            'gt': lambda v, t: v > t,
            'gte': lambda v, t: v >= t,
            'lt': lambda v, t: v < t,
            'lte': lambda v, t: v <= t,
            'eq': lambda v, t: v == t,
            'ne': lambda v, t: v != t
        }
        
        operator_func = operators.get(alert.operator)
        if not operator_func:
            logger.error(f"Unknown operator in alert {alert.name}: {alert.operator}")
            return False
        
        return operator_func(value, alert.threshold)
    
    def _trigger_alert(self, alert: Alert, current_value: float):
        """Trigger an alert."""
        alert_data = {
            'name': alert.name,
            'severity': alert.severity,
            'condition': alert.condition,
            'threshold': alert.threshold,
            'current_value': current_value,
            'timestamp': datetime.now().isoformat(),
            'description': alert.description
        }
        
        # Add to history
        self.alert_history.append(alert_data)
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
        
        logger.warning(f"ALERT: {alert.name} - {alert.description} (value: {current_value}, threshold: {alert.threshold})")
    
    def _cleanup_old_metrics(self):
        """Clean up old metrics beyond retention period."""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self._lock:
            for name, metric_list in self.metrics.items():
                # Remove old metrics
                while metric_list and metric_list[0].timestamp < cutoff_time:
                    metric_list.popleft()
    
    def add_custom_collector(self, collector: Callable):
        """Add a custom metrics collector function."""
        self.custom_collectors.append(collector)
        logger.info("Custom metrics collector added")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get collector statistics."""
        with self._lock:
            total_metrics = sum(len(metric_list) for metric_list in self.metrics.values())
            
            return {
                'collecting': self._collecting,
                'total_metrics': total_metrics,
                'unique_metrics': len(self.metrics),
                'counters': len(self.counters),
                'gauges': len(self.gauges),
                'histograms': len(self.histograms),
                'alerts': len(self.alerts),
                'active_alerts': len([a for a in self.alerts.values() if a.enabled]),
                'alert_history_count': len(self.alert_history),
                'retention_hours': self.retention_hours,
                'collection_interval': self.collection_interval
            }
    
    def export_metrics(self, format_type: str = 'json') -> str:
        """Export metrics in various formats."""
        if format_type == 'json':
            return json.dumps(self.get_all_metrics(), indent=2)
        elif format_type == 'prometheus':
            return self._export_prometheus()
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        with self._lock:
            for name, metric_list in self.metrics.items():
                if not metric_list:
                    continue
                
                latest = metric_list[-1]
                metric_name = name.replace('.', '_').replace('-', '_')
                
                # Add help and type comments
                lines.append(f"# HELP {metric_name} {name}")
                lines.append(f"# TYPE {metric_name} gauge")
                
                # Add metric value with labels
                labels_str = ""
                if latest.labels:
                    label_pairs = [f'{k}="{v}"' for k, v in latest.labels.items()]
                    labels_str = "{" + ",".join(label_pairs) + "}"
                
                lines.append(f"{metric_name}{labels_str} {latest.value}")
        
        return "\n".join(lines)


class HealthChecker:
    """
    Health checking system for application components.
    
    Provides health checks for various application components
    and external dependencies.
    """
    
    def __init__(self):
        """Initialize health checker."""
        self.health_checks = {}
        self.last_results = {}
        self._lock = threading.RLock()
        
        logger.info("HealthChecker initialized")
    
    def add_health_check(self, name: str, check_func: Callable, timeout: float = 5.0):
        """
        Add a health check.
        
        Args:
            name: Name of the health check
            check_func: Function that returns True if healthy
            timeout: Timeout for the check in seconds
        """
        self.health_checks[name] = {
            'function': check_func,
            'timeout': timeout
        }
        logger.info(f"Health check added: {name}")
    
    def remove_health_check(self, name: str):
        """Remove a health check."""
        with self._lock:
            if name in self.health_checks:
                del self.health_checks[name]
                self.last_results.pop(name, None)
                logger.info(f"Health check removed: {name}")
    
    def check_health(self, name: Optional[str] = None) -> Dict[str, Any]:
        """
        Run health checks.
        
        Args:
            name: Specific check to run, or None for all checks
            
        Returns:
            Dict with health check results
        """
        if name:
            return self._run_single_check(name)
        else:
            return self._run_all_checks()
    
    def _run_single_check(self, name: str) -> Dict[str, Any]:
        """Run a single health check."""
        if name not in self.health_checks:
            return {
                'status': 'unknown',
                'error': f'Health check {name} not found'
            }
        
        check_config = self.health_checks[name]
        result = self._execute_check(name, check_config)
        
        with self._lock:
            self.last_results[name] = result
        
        return {name: result}
    
    def _run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks."""
        results = {}
        overall_status = 'healthy'
        
        for name, check_config in self.health_checks.items():
            result = self._execute_check(name, check_config)
            results[name] = result
            
            if result['status'] != 'healthy':
                overall_status = 'unhealthy'
        
        with self._lock:
            self.last_results.update(results)
        
        return {
            'overall_status': overall_status,
            'checks': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def _execute_check(self, name: str, check_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single health check."""
        start_time = time.time()
        
        try:
            check_func = check_config['function']
            timeout = check_config['timeout']
            
            # Run check with timeout
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Health check {name} timed out after {timeout}s")
            
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            
            try:
                is_healthy = check_func()
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                
                execution_time = time.time() - start_time
                
                return {
                    'status': 'healthy' if is_healthy else 'unhealthy',
                    'execution_time': execution_time,
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
                raise e
                
        except Exception as e:
            execution_time = time.time() - start_time
            
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': execution_time,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_last_results(self) -> Dict[str, Any]:
        """Get the last health check results."""
        with self._lock:
            return dict(self.last_results)
    
    def is_healthy(self, name: Optional[str] = None) -> bool:
        """Check if component(s) are healthy."""
        if name:
            result = self.last_results.get(name, {})
            return result.get('status') == 'healthy'
        else:
            return all(
                result.get('status') == 'healthy'
                for result in self.last_results.values()
            )


# Global instances
metrics_collector = MetricsCollector()
health_checker = HealthChecker()


# Default health checks
def _database_health_check():
    """Check database connectivity."""
    try:
        # This would check actual database connection
        # For now, just return True
        return True
    except Exception:
        return False


def _storage_health_check():
    """Check storage system health."""
    try:
        # Check if we can read/write to storage
        import tempfile
        import os
        
        # Try to create a temporary file
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b'health_check')
            tmp.flush()
            return os.path.exists(tmp.name)
    except Exception:
        return False


def _memory_health_check():
    """Check memory usage health."""
    try:
        process = psutil.Process()
        memory_percent = process.memory_percent()
        return memory_percent < 90.0  # Alert if using more than 90% of available memory
    except Exception:
        return False


# Add default health checks
health_checker.add_health_check('storage', _storage_health_check)
health_checker.add_health_check('memory', _memory_health_check)


# Default alerts
default_alerts = [
    Alert(
        name='high_memory_usage',
        condition='system.memory.percent',
        threshold=80.0,
        operator='gt',
        severity='warning',
        description='Memory usage is above 80%'
    ),
    Alert(
        name='critical_memory_usage',
        condition='system.memory.percent',
        threshold=90.0,
        operator='gt',
        severity='critical',
        description='Memory usage is above 90%'
    ),
    Alert(
        name='high_cpu_usage',
        condition='system.cpu.percent',
        threshold=80.0,
        operator='gt',
        severity='warning',
        description='CPU usage is above 80%'
    ),
    Alert(
        name='high_error_rate',
        condition='app.requests.errors',
        threshold=10.0,
        operator='gt',
        severity='critical',
        description='Error rate is too high'
    )
]

# Add default alerts
for alert in default_alerts:
    metrics_collector.add_alert(alert)








