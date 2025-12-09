"""
Monitoring and health check router for the Hybrid Chatbot System
Provides Prometheus metrics endpoint and health checks
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
import psutil
import time
from typing import Dict, Any

from database.session import get_db
from api.schemas.auth import TokenData
from core.security import verify_token
from core.config import settings
from workers.worker_manager import worker_manager
from monitoring.metrics import (
    record_request_metrics, record_worker_metrics, 
    update_system_metrics, update_active_connections
)

router = APIRouter()

# Prometheus metrics endpoint
@router.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    
    # Update system metrics
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    update_system_metrics(memory.used, cpu_percent)
    
    # Update worker metrics
    for worker_type in ["llm", "web", "embedding"]:
        # This would be updated based on actual worker counts
        pass
    
    return PlainTextResponse(content=generate_latest().decode("utf-8"), media_type=CONTENT_TYPE_LATEST)


@router.get("/health")
async def health_check():
    """Comprehensive health check"""
    try:
        # Check basic system status
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Check worker manager status
        is_worker_monitoring = (
            worker_manager._monitor_task is not None 
            and not worker_manager._monitor_task.done()
        )
        
        # Check Redis connection if available
        redis_connected = worker_manager.registry._redis_client is not None
        if redis_connected:
            try:
                await worker_manager.registry._redis_client.ping()
            except:
                redis_connected = False
        
        # Get worker statistics
        total_workers = len(worker_manager.registry._workers)
        active_workers = len([w for w in worker_manager.registry._workers.values()])
        
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available": memory.available,
                "memory_total": memory.total
            },
            "components": {
                "api_gateway": True,
                "worker_manager": is_worker_monitoring,
                "redis_connection": redis_connected,
                "database": True  # Assuming DB is OK if we reach this point
            },
            "workers": {
                "total_registered": total_workers,
                "active": active_workers,
                "monitoring_active": is_worker_monitoring
            }
        }
        
        # Check if system is under high load
        if cpu_percent > 80 or memory.percent > 80:
            health_status["status"] = "warning"
            health_status["message"] = "High system load detected"
        
        return health_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/system-stats")
async def get_system_stats(current_user: TokenData = Depends(verify_token)):
    """Get detailed system statistics"""
    try:
        # System stats
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk_usage = psutil.disk_usage('/')
        
        # Process stats
        process = psutil.Process()
        process_memory = process.memory_info().rss
        process_cpu = process.cpu_percent()
        
        # Worker stats
        total_workers = len(worker_manager.registry._workers)
        active_workers = len([w for w in worker_manager.registry._workers.values()])
        
        # Get worker details
        worker_details = []
        for worker_id, worker_info in worker_manager.registry._workers.items():
            load = worker_manager.registry.get_worker_load(worker_id)
            worker_details.append({
                "worker_id": worker_id,
                "worker_type": worker_info.worker_type.value,
                "hostname": worker_info.hostname,
                "ip_address": worker_info.ip_address,
                "gpu_info": worker_info.gpu_info,
                "max_concurrent_tasks": worker_info.max_concurrent_tasks,
                "current_load": load,
                "capabilities": worker_info.capabilities
            })
        
        stats = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used": memory.used,
                "memory_total": memory.total,
                "memory_available": memory.available,
                "disk_percent": disk_usage.percent,
                "disk_used": disk_usage.used,
                "disk_total": disk_usage.total,
                "process_memory": process_memory,
                "process_cpu": process_cpu
            },
            "workers": {
                "total": total_workers,
                "active": active_workers,
                "details": worker_details
            },
            "timestamp": time.time()
        }
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting system stats: {str(e)}"
        )


@router.get("/workers-discovery")
async def discover_workers(current_user: TokenData = Depends(verify_token)):
    """Discover workers in the local network"""
    try:
        discovered_workers = await worker_manager.registry.discover_workers()
        return {
            "discovered_workers": discovered_workers,
            "count": len(discovered_workers),
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error discovering workers: {str(e)}"
        )


@router.get("/queue-status")
async def get_queue_status(current_user: TokenData = Depends(verify_token)):
    """Get task queue status"""
    try:
        # This would check Redis queue status in a real implementation
        if worker_manager.registry._redis_client:
            try:
                # Get length of task queue
                queue_length = await worker_manager.registry._redis_client.xlen(worker_manager.registry._task_queue)
                
                # Get length of dead letter queue
                dlq_length = await worker_manager.registry._redis_client.xlen(worker_manager.registry._dead_letter_queue)
                
                queue_status = {
                    "task_queue_length": queue_length,
                    "dead_letter_queue_length": dlq_length,
                    "redis_connected": True,
                    "timestamp": time.time()
                }
            except:
                queue_status = {
                    "task_queue_length": "unknown",
                    "dead_letter_queue_length": "unknown",
                    "redis_connected": False,
                    "timestamp": time.time()
                }
        else:
            queue_status = {
                "task_queue_length": "unknown",
                "dead_letter_queue_length": "unknown",
                "redis_connected": False,
                "timestamp": time.time()
            }
        
        return queue_status
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting queue status: {str(e)}"
        )