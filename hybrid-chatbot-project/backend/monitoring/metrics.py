"""
Metrics collection module for the Hybrid Chatbot System
Integrates with Prometheus for system monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, Summary
import time
from typing import Dict, Any

# Request metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Worker metrics
WORKER_COUNT = Gauge(
    'workers_total',
    'Total number of registered workers',
    ['worker_type']
)

WORKER_TASKS = Gauge(
    'worker_active_tasks',
    'Number of active tasks per worker',
    ['worker_id', 'worker_type']
)

WORKER_HEALTH = Gauge(
    'worker_health_status',
    'Health status of workers (1=healthy, 0=unhealthy)',
    ['worker_id']
)

# Task metrics
TASK_QUEUE_SIZE = Gauge(
    'task_queue_size',
    'Current size of task queue',
    ['task_type']
)

TASK_PROCESSED = Counter(
    'tasks_processed_total',
    'Total number of processed tasks',
    ['task_type', 'status']  # status: success, error, timeout
)

TASK_DURATION = Histogram(
    'task_duration_seconds',
    'Task processing duration in seconds',
    ['task_type']
)

# System metrics
ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active WebSocket connections'
)

MEMORY_USAGE = Gauge(
    'memory_usage_bytes',
    'Memory usage in bytes'
)

CPU_USAGE = Gauge(
    'cpu_usage_percent',
    'CPU usage percentage'
)

# Database metrics
DB_CONNECTIONS = Gauge(
    'db_connections',
    'Number of active database connections'
)

DB_QUERY_DURATION = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds'
)

def record_request_metrics(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics"""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

def record_worker_metrics(worker_type: str, count: int):
    """Record worker metrics"""
    WORKER_COUNT.labels(worker_type=worker_type).set(count)

def record_worker_task_count(worker_id: str, worker_type: str, count: int):
    """Record active tasks per worker"""
    WORKER_TASKS.labels(worker_id=worker_id, worker_type=worker_type).set(count)

def record_task_queue_size(task_type: str, size: int):
    """Record task queue size"""
    TASK_QUEUE_SIZE.labels(task_type=task_type).set(size)

def record_task_processed(task_type: str, status: str, duration: float = None):
    """Record task processing metrics"""
    TASK_PROCESSED.labels(task_type=task_type, status=status).inc()
    if duration:
        TASK_DURATION.labels(task_type=task_type).observe(duration)

def update_worker_health(worker_id: str, is_healthy: bool):
    """Update worker health status"""
    WORKER_HEALTH.labels(worker_id=worker_id).set(1 if is_healthy else 0)

def update_active_connections(count: int):
    """Update active WebSocket connections count"""
    ACTIVE_CONNECTIONS.set(count)

def update_system_metrics(memory_usage: int, cpu_usage: float):
    """Update system resource metrics"""
    MEMORY_USAGE.set(memory_usage)
    CPU_USAGE.set(cpu_usage)

def update_db_connections(count: int):
    """Update database connections count"""
    DB_CONNECTIONS.set(count)

def record_db_query_duration(duration: float):
    """Record database query duration"""
    DB_QUERY_DURATION.observe(duration)