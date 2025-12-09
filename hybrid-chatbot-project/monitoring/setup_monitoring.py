#!/usr/bin/env python3
"""
Monitoring setup for Hybrid Chatbot System
Configures Grafana dashboards, alerting, and monitoring systems
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MonitoringSetup:
    """Setup class for monitoring systems"""
    
    def __init__(self):
        self.monitoring_dir = project_root / "monitoring"
        self.dashboards_dir = self.monitoring_dir / "dashboards"
        self.alerts_dir = self.monitoring_dir / "alerts"
        self.config_dir = self.monitoring_dir / "config"
        
        # Create directories
        self.dashboards_dir.mkdir(exist_ok=True)
        self.alerts_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)
    
    def create_grafana_dashboards(self) -> Dict[str, str]:
        """Create Grafana dashboards for system monitoring"""
        print("Creating Grafana dashboards...")
        
        dashboards = {
            "system_overview": self._create_system_overview_dashboard(),
            "worker_performance": self._create_worker_performance_dashboard(),
            "api_performance": self._create_api_performance_dashboard(),
            "database_monitoring": self._create_database_monitoring_dashboard(),
            "security_monitoring": self._create_security_monitoring_dashboard(),
        }
        
        dashboard_paths = {}
        for name, dashboard in dashboards.items():
            dashboard_path = self.dashboards_dir / f"{name}.json"
            with open(dashboard_path, 'w') as f:
                json.dump(dashboard, f, indent=2)
            dashboard_paths[name] = str(dashboard_path)
        
        print(f"  Created {len(dashboards)} Grafana dashboards")
        return dashboard_paths
    
    def _create_system_overview_dashboard(self) -> Dict[str, Any]:
        """Create system overview dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "System Overview - Hybrid Chatbot",
                "tags": ["hybrid-chatbot", "overview", "system"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "System Health Status",
                        "type": "stat",
                        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "up{job=\"hybrid-chatbot-api\"}",
                                "legendFormat": "API Status"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "thresholds"
                                },
                                "thresholds": {
                                    "steps": [
                                        {"color": "red", "value": 0},
                                        {"color": "green", "value": 1}
                                    ]
                                }
                            }
                        }
                    },
                    {
                        "id": 2,
                        "title": "Active Connections",
                        "type": "gauge",
                        "gridPos": {"h": 8, "w": 6, "x": 6, "y": 0},
                        "targets": [
                            {
                                "expr": "chat_active_connections",
                                "legendFormat": "Active Connections"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                },
                                "min": 0,
                                "max": 2000
                            }
                        }
                    },
                    {
                        "id": 3,
                        "title": "API Response Time (95th percentile)",
                        "type": "graph",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m]))",
                                "legendFormat": "Response Time (95th percentile)"
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "Worker Status",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 12, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": "count(worker_status{status=\"active\"})",
                                "legendFormat": "Active Workers"
                            },
                            {
                                "expr": "count(worker_status{status=\"offline\"})",
                                "legendFormat": "Offline Workers"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                }
                            },
                            "overrides": [
                                {
                                    "matcher": {"id": "byName", "options": "Active Workers"},
                                    "properties": [
                                        {"id": "color", "value": {"fixedColor": "green", "mode": "fixed"}}
                                    ]
                                },
                                {
                                    "matcher": {"id": "byName", "options": "Offline Workers"},
                                    "properties": [
                                        {"id": "color", "value": {"fixedColor": "red", "mode": "fixed"}}
                                    ]
                                }
                            ]
                        }
                    },
                    {
                        "id": 5,
                        "title": "System Resource Usage",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                        "targets": [
                            {
                                "expr": "100 - (avg by(instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
                                "legendFormat": "CPU Usage"
                            },
                            {
                                "expr": "(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100",
                                "legendFormat": "Memory Usage"
                            }
                        ]
                    }
                ],
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "30s"
            },
            "folderId": 0,
            "overwrite": False
        }
    
    def _create_worker_performance_dashboard(self) -> Dict[str, Any]:
        """Create worker performance dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "Worker Performance - Hybrid Chatbot",
                "tags": ["hybrid-chatbot", "workers", "performance"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Worker Load Distribution",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "worker_active_tasks",
                                "legendFormat": "{{worker_id}}"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Worker Response Times",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(worker_response_time_seconds_bucket[5m])) by (worker_id)",
                                "legendFormat": "{{worker_id}}"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Worker Status by Type",
                        "type": "stat",
                        "gridPos": {"h": 6, "w": 8, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": "count(worker_status{type=\"llm\"})",
                                "legendFormat": "LLM Workers"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "thresholds"
                                },
                                "displayName": "LLM Workers"
                            }
                        }
                    },
                    {
                        "id": 4,
                        "title": "GPU Utilization",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 16, "x": 8, "y": 8},
                        "targets": [
                            {
                                "expr": "gpu_utilization",
                                "legendFormat": "{{gpu_model}}"
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "Worker Error Rates",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                        "targets": [
                            {
                                "expr": "rate(worker_errors_total[5m])",
                                "legendFormat": "{{worker_id}}"
                            }
                        ]
                    },
                    {
                        "id": 6,
                        "title": "Task Completion Rates",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                        "targets": [
                            {
                                "expr": "rate(worker_tasks_completed_total[5m])",
                                "legendFormat": "{{worker_id}}"
                            }
                        ]
                    }
                ],
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "30s"
            },
            "folderId": 0,
            "overwrite": False
        }
    
    def _create_api_performance_dashboard(self) -> Dict[str, Any]:
        """Create API performance dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "API Performance - Hybrid Chatbot",
                "tags": ["hybrid-chatbot", "api", "performance"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "API Request Rate",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(api_requests_total[5m])",
                                "legendFormat": "{{handler}}"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "API Response Time",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            },
                            {
                                "expr": "histogram_quantile(0.99, rate(api_response_time_seconds_bucket[5m]))",
                                "legendFormat": "99th percentile"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "API Error Rate",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": "rate(api_errors_total[5m])",
                                "legendFormat": "{{handler}}"
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "Active WebSocket Connections",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                        "targets": [
                            {
                                "expr": "chat_active_connections",
                                "legendFormat": "Active Connections"
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "Concurrent Users",
                        "type": "gauge",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                        "targets": [
                            {
                                "expr": "count(count by (user_id) (chat_active_connections))",
                                "legendFormat": "Concurrent Users"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                },
                                "min": 0,
                                "max": 2000
                            }
                        }
                    },
                    {
                        "id": 6,
                        "title": "Message Processing Rate",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                        "targets": [
                            {
                                "expr": "rate(chat_messages_processed_total[5m])",
                                "legendFormat": "Messages per second"
                            }
                        ]
                    }
                ],
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "30s"
            },
            "folderId": 0,
            "overwrite": False
        }
    
    def _create_database_monitoring_dashboard(self) -> Dict[str, Any]:
        """Create database monitoring dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "Database Monitoring - Hybrid Chatbot",
                "tags": ["hybrid-chatbot", "database", "mysql", "redis"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "MySQL Connections",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "mysql_global_status_threads_connected",
                                "legendFormat": "Connected Threads"
                            },
                            {
                                "expr": "mysql_global_status_threads_running",
                                "legendFormat": "Running Threads"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "MySQL Query Performance",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(mysql_global_status_questions[5m])",
                                "legendFormat": "Queries per second"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Redis Memory Usage",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": "redis_memory_used_bytes",
                                "legendFormat": "Used Memory"
                            },
                            {
                                "expr": "redis_memory_max_bytes",
                                "legendFormat": "Max Memory"
                            }
                        ]
                    },
                    {
                        "id": 4,
                        "title": "Redis Operations",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                        "targets": [
                            {
                                "expr": "rate(redis_commands_processed_total[5m])",
                                "legendFormat": "Commands per second"
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "Database Connection Pool",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                        "targets": [
                            {
                                "expr": "database_connections_used",
                                "legendFormat": "Used Connections"
                            },
                            {
                                "expr": "database_connections_total",
                                "legendFormat": "Total Connections"
                            }
                        ]
                    },
                    {
                        "id": 6,
                        "title": "Database Query Duration",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                        "targets": [
                            {
                                "expr": "histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m]))",
                                "legendFormat": "95th percentile"
                            }
                        ]
                    }
                ],
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "30s"
            },
            "folderId": 0,
            "overwrite": False
        }
    
    def _create_security_monitoring_dashboard(self) -> Dict[str, Any]:
        """Create security monitoring dashboard"""
        return {
            "dashboard": {
                "id": None,
                "title": "Security Monitoring - Hybrid Chatbot",
                "tags": ["hybrid-chatbot", "security", "auth", "logs"],
                "style": "dark",
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Authentication Attempts",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
                        "targets": [
                            {
                                "expr": "rate(auth_attempts_total[5m])",
                                "legendFormat": "Total Attempts"
                            },
                            {
                                "expr": "rate(auth_failures_total[5m])",
                                "legendFormat": "Failed Attempts"
                            }
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Failed Login Attempts by IP",
                        "type": "table",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
                        "targets": [
                            {
                                "expr": "sum by (source_ip) (rate(auth_failures_total[10m])) > 5",
                                "legendFormat": "Failed Attempts by IP"
                            }
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Active Sessions",
                        "type": "gauge",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
                        "targets": [
                            {
                                "expr": "auth_active_sessions",
                                "legendFormat": "Active Sessions"
                            }
                        ],
                        "fieldConfig": {
                            "defaults": {
                                "color": {
                                    "mode": "palette-classic"
                                },
                                "min": 0,
                                "max": 5000
                            }
                        }
                    },
                    {
                        "id": 4,
                        "title": "API Rate Limiting",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
                        "targets": [
                            {
                                "expr": "rate(api_rate_limit_exceeded_total[5m])",
                                "legendFormat": "Rate Limit Exceeded"
                            }
                        ]
                    },
                    {
                        "id": 5,
                        "title": "Security Events",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
                        "targets": [
                            {
                                "expr": "rate(security_events_total[5m])",
                                "legendFormat": "{{event_type}}"
                            }
                        ]
                    },
                    {
                        "id": 6,
                        "title": "Token Expiration Rate",
                        "type": "timeseries",
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
                        "targets": [
                            {
                                "expr": "rate(token_expirations_total[5m])",
                                "legendFormat": "Expired Tokens"
                            }
                        ]
                    }
                ],
                "time": {"from": "now-6h", "to": "now"},
                "refresh": "30s"
            },
            "folderId": 0,
            "overwrite": False
        }
    
    def create_alerting_rules(self) -> Dict[str, str]:
        """Create alerting rules for monitoring"""
        print("Creating alerting rules...")
        
        alerts = {
            "system_health": self._create_system_health_alerts(),
            "performance": self._create_performance_alerts(),
            "security": self._create_security_alerts(),
            "workers": self._create_worker_alerts(),
        }
        
        alert_paths = {}
        for name, alert_config in alerts.items():
            alert_path = self.alerts_dir / f"{name}_alerts.yml"
            with open(alert_path, 'w') as f:
                f.write(alert_config)
            alert_paths[name] = str(alert_path)
        
        print(f"  Created {len(alerts)} alerting rule configurations")
        return alert_paths
    
    def _create_system_health_alerts(self) -> str:
        """Create system health alerting rules"""
        return """groups:
- name: system_health
  rules:
  - alert: APIDown
    expr: up{job="hybrid-chatbot-api"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "API is down"
      description: "The Hybrid Chatbot API has been down for more than 2 minutes"

  - alert: HighErrorRate
    expr: rate(api_errors_total[5m]) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"
      description: "API error rate is above 10 errors per minute"

  - alert: DatabaseDown
    expr: up{job="mysql"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Database is down"
      description: "The database connection is unavailable"

  - alert: RedisDown
    expr: up{job="redis"} == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Redis is down"
      description: "The Redis cache is unavailable"

  - alert: HighMemoryUsage
    expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage"
      description: "Memory usage is above 90%"

  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 90
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High CPU usage"
      description: "CPU usage is above 90%"
"""
    
    def _create_performance_alerts(self) -> str:
        """Create performance alerting rules"""
        return """groups:
- name: performance
  rules:
  - alert: HighResponseTime
    expr: histogram_quantile(0.95, rate(api_response_time_seconds_bucket[5m])) > 2
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High API response time"
      description: "95th percentile of API response time is above 2 seconds"

  - alert: LowThroughput
    expr: rate(api_requests_total[5m]) < 10
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Low API throughput"
      description: "API request rate is below 10 requests per minute (possible issue)"

  - alert: HighWebSocketConnections
    expr: chat_active_connections > 1500
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "High WebSocket connections"
      description: "Active WebSocket connections exceeded 1500"

  - alert: DatabaseSlowQueries
    expr: histogram_quantile(0.95, rate(database_query_duration_seconds_bucket[5m])) > 1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Slow database queries"
      description: "95th percentile of database query time is above 1 second"

  - alert: CacheMissRateHigh
    expr: rate(redis_keyspace_misses_total[5m]) / rate(redis_commands_processed_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High cache miss rate"
      description: "Cache miss rate is above 10%"
"""
    
    def _create_security_alerts(self) -> str:
        """Create security alerting rules"""
        return """groups:
- name: security
  rules:
  - alert: HighAuthFailureRate
    expr: rate(auth_failures_total[5m]) > 20
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High authentication failure rate"
      description: "More than 20 authentication failures per minute"

  - alert: PotentialBruteForce
    expr: rate(auth_failures_total[10m]) > 50
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Potential brute force attack"
      description: "More than 50 failed authentication attempts in 10 minutes from a single source"

  - alert: RateLimitExceeded
    expr: rate(api_rate_limit_exceeded_total[5m]) > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High rate limit exceeded events"
      description: "More than 100 rate limit exceeded events per minute"

  - alert: SecurityEventSpikes
    expr: rate(security_events_total[5m]) > 50
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High security event rate"
      description: "More than 50 security events per minute"

  - alert: UnauthorizedAccessAttempt
    expr: rate(api_unauthorized_requests_total[5m]) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High unauthorized access attempts"
      description: "More than 5 unauthorized access attempts per minute"
"""
    
    def _create_worker_alerts(self) -> str:
        """Create worker alerting rules"""
        return """groups:
- name: workers
  rules:
  - alert: WorkerOffline
    expr: count(worker_status{status="offline"}) > 0
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Worker(s) offline"
      description: "{{ $value }} worker(s) are offline"

  - alert: HighWorkerErrorRate
    expr: rate(worker_errors_total[5m]) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High worker error rate"
      description: "Worker error rate is above 5 errors per minute"

  - alert: WorkerResponseTimeHigh
    expr: histogram_quantile(0.95, rate(worker_response_time_seconds_bucket[5m])) > 5
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High worker response time"
      description: "95th percentile of worker response time is above 5 seconds"

  - alert: LowWorkerAvailability
    expr: count(worker_status{status="active"}) < 2
    for: 10m
    labels:
      severity: critical
    annotations:
      summary: "Low worker availability"
      description: "Less than 2 workers are active, system may be overloaded"

  - alert: GPUHighUtilization
    expr: gpu_utilization > 95
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High GPU utilization"
      description: "GPU utilization is above 95%"
"""
    
    def create_monitoring_config(self) -> str:
        """Create monitoring configuration files"""
        print("Creating monitoring configuration...")
        
        # Prometheus configuration
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": [
                str(self.alerts_dir / "system_health_alerts.yml"),
                str(self.alerts_dir / "performance_alerts.yml"),
                str(self.alerts_dir / "security_alerts.yml"),
                str(self.alerts_dir / "worker_alerts.yml")
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": ["alertmanager:9093"]
                            }
                        ]
                    }
                ]
            },
            "scrape_configs": [
                {
                    "job_name": "hybrid-chatbot-api",
                    "static_configs": [
                        {
                            "targets": ["localhost:8000"]
                        }
                    ]
                },
                {
                    "job_name": "node",
                    "static_configs": [
                        {
                            "targets": ["localhost:9100"]
                        }
                    ]
                },
                {
                    "job_name": "mysql",
                    "static_configs": [
                        {
                            "targets": ["localhost:9104"]
                        }
                    ]
                },
                {
                    "job_name": "redis",
                    "static_configs": [
                        {
                            "targets": ["localhost:9121"]
                        }
                    ]
                }
            ]
        }
        
        prometheus_config_path = self.config_dir / "prometheus.yml"
        with open(prometheus_config_path, 'w') as f:
            json.dump(prometheus_config, f, indent=2)
        
        print(f"  Created Prometheus configuration: {prometheus_config_path}")
        return str(prometheus_config_path)
    
    def create_admin_panel_config(self) -> str:
        """Create admin panel configuration"""
        print("Creating admin panel configuration...")
        
        admin_config = {
            "dashboard": {
                "title": "Hybrid Chatbot Admin Panel",
                "version": 1,
                "panels": [
                    {
                        "id": 1,
                        "title": "System Status",
                        "type": "stat",
                        "targets": [
                            {"expr": "up{job='hybrid-chatbot-api'}", "legend": "API Status"}
                        ]
                    },
                    {
                        "id": 2,
                        "title": "Active Users",
                        "type": "gauge",
                        "targets": [
                            {"expr": "count(count by (user_id) (chat_active_connections))", "legend": "Concurrent Users"}
                        ]
                    },
                    {
                        "id": 3,
                        "title": "Worker Status",
                        "type": "stat",
                        "targets": [
                            {"expr": "count(worker_status{status='active'})", "legend": "Active Workers"},
                            {"expr": "count(worker_status{status='offline'})", "legend": "Offline Workers"}
                        ]
                    }
                ]
            },
            "refresh_intervals": ["5s", "10s", "30s", "1m", "5m"],
            "time_options": ["5m", "15m", "1h", "6h", "12h", "24h", "2d", "7d", "30d"]
        }
        
        admin_config_path = self.config_dir / "admin_panel.json"
        with open(admin_config_path, 'w') as f:
            json.dump(admin_config, f, indent=2)
        
        print(f"  Created admin panel configuration: {admin_config_path}")
        return str(admin_config_path)
    
    def setup_monitoring_system(self) -> Dict[str, Any]:
        """Main method to setup the monitoring system"""
        print("Setting up monitoring system for Hybrid Chatbot...")
        print("=" * 60)
        
        # Create Grafana dashboards
        dashboards = self.create_grafana_dashboards()
        
        # Create alerting rules
        alerts = self.create_alerting_rules()
        
        # Create monitoring configuration
        prometheus_config = self.create_monitoring_config()
        
        # Create admin panel configuration
        admin_config = self.create_admin_panel_config()
        
        setup_info = {
            "dashboards": dashboards,
            "alerts": alerts,
            "prometheus_config": prometheus_config,
            "admin_config": admin_config,
            "timestamp": datetime.now().isoformat()
        }
        
        print("=" * 60)
        print("Monitoring system setup completed successfully!")
        print(f"Dashboards created: {len(dashboards)}")
        print(f"Alert rules created: {len(alerts)}")
        print(f"Configuration files: 2")
        
        return setup_info


def main():
    """Main function to run the monitoring setup"""
    monitor = MonitoringSetup()
    result = monitor.setup_monitoring_system()
    
    print(f"\n✓ Monitoring setup completed!")
    print(f"✓ Dashboards: {list(result['dashboards'].keys())}")
    print(f"✓ Alert configs: {list(result['alerts'].keys())}")
    print(f"✓ Prometheus config: {result['prometheus_config']}")
    print(f"✓ Admin config: {result['admin_config']}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())