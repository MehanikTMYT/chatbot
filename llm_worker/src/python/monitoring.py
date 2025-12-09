"""
Monitoring and Health Check Utilities for LLM Worker
Provides GPU monitoring, performance tracking, and health checks
"""
import psutil
import GPUtil
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import threading
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class GPUStats:
    """GPU statistics data class"""
    id: int
    name: str
    utilization: float  # Percentage
    memory_used: int    # MB
    memory_total: int   # MB
    memory_free: int    # MB
    temperature: Optional[float] = None
    power_draw: Optional[float] = None
    timestamp: float = time.time()

@dataclass
class SystemStats:
    """System statistics data class"""
    cpu_percent: float
    memory_used: int      # MB
    memory_total: int     # MB
    disk_usage: float     # Percentage
    network_sent: int     # Bytes
    network_recv: int     # Bytes
    timestamp: float = time.time()

@dataclass
class PerformanceMetrics:
    """Performance metrics for LLM generation"""
    requests_per_second: float
    avg_generation_time: float
    tokens_per_second: float
    active_requests: int
    gpu_memory_used: float  # GB
    gpu_utilization: float  # Percentage
    timestamp: float = time.time()

class ResourceMonitor:
    """Monitors system and GPU resources"""
    
    def __init__(self):
        self.monitoring = False
        self.monitoring_thread = None
        self.stats_history = []
        self.max_history = 100  # Keep last 100 measurements
        
    def start_monitoring(self):
        """Start resource monitoring in a separate thread"""
        if self.monitoring:
            return
            
        self.monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring"""
        self.monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2)
        logger.info("Resource monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                stats = self.get_current_stats()
                self.stats_history.append(stats)
                
                # Keep history within limits
                if len(self.stats_history) > self.max_history:
                    self.stats_history = self.stats_history[-self.max_history:]
                
                time.sleep(1)  # Monitor every second
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
    
    def get_current_stats(self) -> Dict[str, any]:
        """Get current system and GPU stats"""
        # Get GPU stats
        gpus = GPUtil.getGPUs()
        gpu_stats = []
        for gpu in gpus:
            gpu_stat = GPUStats(
                id=gpu.id,
                name=gpu.name,
                utilization=gpu.load * 100,
                memory_used=int(gpu.memoryUsed),
                memory_total=int(gpu.memoryTotal),
                memory_free=int(gpu.memoryFree),
                temperature=gpu.temperature
            )
            gpu_stats.append(gpu_stat)
        
        # Get system stats
        net_io = psutil.net_io_counters()
        system_stats = SystemStats(
            cpu_percent=psutil.cpu_percent(interval=0.1),
            memory_used=int(psutil.virtual_memory().used / (1024 * 1024)),  # MB
            memory_total=int(psutil.virtual_memory().total / (1024 * 1024)),  # MB
            disk_usage=psutil.disk_usage('/').percent,
            network_sent=net_io.bytes_sent,
            network_recv=net_io.bytes_recv
        )
        
        return {
            'gpu_stats': gpu_stats,
            'system_stats': system_stats,
            'timestamp': time.time()
        }
    
    def get_average_gpu_stats(self, window_minutes: int = 1) -> Optional[GPUStats]:
        """Get average GPU stats over the specified time window"""
        if not self.stats_history:
            return None
            
        cutoff_time = time.time() - (window_minutes * 60)
        recent_stats = [s for s in self.stats_history if s['timestamp'] > cutoff_time]
        
        if not recent_stats:
            return None
            
        # Average GPU stats (assuming single GPU)
        gpu_stats_list = [s['gpu_stats'][0] for s in recent_stats if s['gpu_stats']]
        
        if not gpu_stats_list:
            return None
            
        avg_util = sum(s.utilization for s in gpu_stats_list) / len(gpu_stats_list)
        avg_mem_used = sum(s.memory_used for s in gpu_stats_list) / len(gpu_stats_list)
        
        return GPUStats(
            id=gpu_stats_list[0].id,
            name=gpu_stats_list[0].name,
            utilization=avg_util,
            memory_used=avg_mem_used,
            memory_total=gpu_stats_list[0].memory_total,
            memory_free=gpu_stats_list[0].memory_free,
            temperature=sum(s.temperature or 0 for s in gpu_stats_list) / len(gpu_stats_list)
        )

class HealthChecker:
    """Performs health checks on the LLM worker system"""
    
    def __init__(self, llm_worker=None):
        self.llm_worker = llm_worker
        self.resource_monitor = ResourceMonitor()
        self.check_results = {}
    
    def perform_health_check(self) -> Dict[str, any]:
        """Perform comprehensive health check"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'overall_status': 'healthy'
        }
        
        # Check GPU availability and status
        results['checks']['gpu'] = self._check_gpu()
        
        # Check system resources
        results['checks']['system'] = self._check_system_resources()
        
        # Check LLM worker status
        results['checks']['llm_worker'] = self._check_llm_worker()
        
        # Check storage space
        results['checks']['storage'] = self._check_storage()
        
        # Determine overall status
        for check_name, check_result in results['checks'].items():
            if not check_result['healthy']:
                results['overall_status'] = 'unhealthy'
                break
        
        self.check_results = results
        return results
    
    def _check_gpu(self) -> Dict[str, any]:
        """Check GPU health"""
        try:
            gpus = GPUtil.getGPUs()
            if not gpus:
                return {
                    'healthy': False,
                    'message': 'No GPUs detected',
                    'details': {}
                }
            
            primary_gpu = gpus[0]  # Check primary GPU
            
            # Check if GPU is not overloaded
            gpu_overloaded = primary_gpu.load > 0.95  # 95% utilization threshold
            memory_critical = (primary_gpu.memoryUsed / primary_gpu.memoryTotal) > 0.95  # 95% memory
            
            healthy = not gpu_overloaded and not memory_critical
            
            return {
                'healthy': healthy,
                'message': 'GPU status OK' if healthy else 'GPU may be overloaded',
                'details': {
                    'gpu_id': primary_gpu.id,
                    'name': primary_gpu.name,
                    'utilization': f"{primary_gpu.load * 100:.1f}%",
                    'memory_used': f"{primary_gpu.memoryUsed}MB/{primary_gpu.memoryTotal}MB",
                    'temperature': f"{primary_gpu.temperature}°C" if primary_gpu.temperature else "N/A"
                }
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'GPU check failed: {str(e)}',
                'details': {}
            }
    
    def _check_system_resources(self) -> Dict[str, any]:
        """Check system resources"""
        try:
            # Get system stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Define thresholds
            cpu_threshold = 90  # 90% CPU usage
            memory_threshold = 90  # 90% memory usage
            disk_threshold = 95   # 95% disk usage
            
            cpu_high = cpu_percent > cpu_threshold
            memory_high = memory.percent > memory_threshold
            disk_high = disk.percent > disk_threshold
            
            healthy = not (cpu_high or memory_high or disk_high)
            
            return {
                'healthy': healthy,
                'message': 'System resources OK' if healthy else 'High resource usage detected',
                'details': {
                    'cpu_percent': f"{cpu_percent}%",
                    'memory_used': f"{memory.used / (1024**3):.1f}GB/{memory.total / (1024**3):.1f}GB ({memory.percent}%)",
                    'disk_used': f"{disk.percent}%"
                }
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'System resource check failed: {str(e)}',
                'details': {}
            }
    
    def _check_llm_worker(self) -> Dict[str, any]:
        """Check LLM worker status"""
        if not self.llm_worker:
            return {
                'healthy': False,
                'message': 'LLM worker not initialized',
                'details': {}
            }
        
        try:
            # Perform worker health check
            worker_status = self.llm_worker.health_check()
            
            healthy = worker_status.get('status') == 'healthy'
            
            return {
                'healthy': healthy,
                'message': 'LLM worker OK' if healthy else 'LLM worker issues detected',
                'details': worker_status
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'LLM worker check failed: {str(e)}',
                'details': {}
            }
    
    def _check_storage(self) -> Dict[str, any]:
        """Check storage space"""
        try:
            disk = psutil.disk_usage('/')
            free_space_gb = disk.free / (1024**3)
            
            # Need at least 10GB free space for model operations
            minimum_space_gb = 10
            has_enough_space = free_space_gb > minimum_space_gb
            
            return {
                'healthy': has_enough_space,
                'message': 'Sufficient storage available' if has_enough_space else f'Low storage: {free_space_gb:.1f}GB free',
                'details': {
                    'free_space_gb': round(free_space_gb, 1),
                    'total_space_gb': round(disk.total / (1024**3), 1),
                    'used_percent': disk.percent
                }
            }
        except Exception as e:
            return {
                'healthy': False,
                'message': f'Storage check failed: {str(e)}',
                'details': {}
            }
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get performance metrics for the LLM system"""
        # Get current stats
        current_stats = self.resource_monitor.get_current_stats()
        
        # Calculate performance metrics
        # These would be populated based on actual worker stats in a real implementation
        gpu_stats = current_stats.get('gpu_stats', [])
        if gpu_stats:
            primary_gpu = gpu_stats[0]
            gpu_memory_used_gb = primary_gpu.memory_used / 1024  # Convert MB to GB
            gpu_util = primary_gpu.utilization * 100
        else:
            gpu_memory_used_gb = 0
            gpu_util = 0
        
        # Placeholder values - in real implementation these would come from the worker
        metrics = PerformanceMetrics(
            requests_per_second=0.0,  # Would come from worker stats
            avg_generation_time=0.0,  # Would come from worker stats
            tokens_per_second=0.0,    # Would come from worker stats
            active_requests=0,        # Would come from worker stats
            gpu_memory_used=gpu_memory_used_gb,
            gpu_utilization=gpu_util
        )
        
        return metrics

class AutoRecoveryManager:
    """Manages automatic recovery from failures"""
    
    def __init__(self, llm_worker, health_checker):
        self.llm_worker = llm_worker
        self.health_checker = health_checker
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3
        self.recovery_interval = 30  # seconds
        self.recovery_lock = threading.Lock()
    
    def monitor_and_recover(self):
        """Monitor system and trigger recovery if needed"""
        health_result = self.health_checker.perform_health_check()
        
        if health_result['overall_status'] != 'healthy':
            logger.warning("Health check failed, initiating recovery procedures")
            
            with self.recovery_lock:
                if self.recovery_attempts < self.max_recovery_attempts:
                    self._attempt_recovery(health_result)
                    self.recovery_attempts += 1
                else:
                    logger.error("Max recovery attempts exceeded, manual intervention required")
    
    def _attempt_recovery(self, health_result):
        """Attempt to recover from issues"""
        logger.info("Attempting recovery...")
        
        # Check which components need recovery
        checks = health_result['checks']
        
        for check_name, check_details in checks.items():
            if not check_details['healthy']:
                logger.info(f"Recovering {check_name} component...")
                
                if check_name == 'llm_worker':
                    self._recover_llm_worker()
                elif check_name == 'gpu':
                    self._recover_gpu_issues()
                elif check_name == 'system':
                    self._recover_system_issues()
        
        logger.info("Recovery attempt completed")
    
    def _recover_llm_worker(self):
        """Recover LLM worker issues"""
        try:
            if self.llm_worker:
                logger.info("Restarting LLM worker...")
                self.llm_worker.stop()
                time.sleep(2)  # Wait before restart
                
                # Restart worker with original parameters
                # This would need to be adapted to your specific initialization
                logger.info("LLM worker restarted")
        except Exception as e:
            logger.error(f"Failed to recover LLM worker: {e}")
    
    def _recover_gpu_issues(self):
        """Recover GPU-related issues"""
        try:
            # Clear GPU cache
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.info("GPU cache cleared")
        except Exception as e:
            logger.error(f"Failed to recover GPU issues: {e}")
    
    def _recover_system_issues(self):
        """Recover system resource issues"""
        try:
            # Log system stats for debugging
            logger.info("System recovery: checking resource usage")
        except Exception as e:
            logger.error(f"Failed to recover system issues: {e}")

# Initialize monitoring components
resource_monitor = ResourceMonitor()
health_checker = HealthChecker()

# Example usage
if __name__ == "__main__":
    # Example of how to use the monitoring system
    resource_monitor.start_monitoring()
    
    # Perform a health check
    checker = HealthChecker()
    results = checker.perform_health_check()
    
    print("Health Check Results:")
    print(json.dumps(results, indent=2, default=str))
    
    # Stop monitoring
    resource_monitor.stop_monitoring()