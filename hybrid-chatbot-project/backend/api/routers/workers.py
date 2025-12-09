"""
Worker management router for the Hybrid Chatbot System
Handles worker registration, heartbeats, and task assignment
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any
import asyncio

from database.session import get_db
from database.models import Worker, WorkerStatus
from api.schemas.auth import TokenData
from core.security import verify_token
from core.config import settings
from workers.worker_manager import worker_manager, WorkerInfo, WorkerType

router = APIRouter()


@router.post("/register")
async def register_worker(
    worker_info: Dict[str, Any],
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Register a new computational worker in the system"""
    try:
        # Validate required fields
        required_fields = ["worker_id", "worker_type", "hostname", "ip_address", "gpu_info", "capabilities"]
        for field in required_fields:
            if field not in worker_info:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate worker type
        try:
            worker_type = WorkerType(worker_info["worker_type"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid worker type. Must be one of: {[e.value for e in WorkerType]}"
            )
        
        # Create WorkerInfo object
        worker_info_obj = WorkerInfo(
            worker_id=worker_info["worker_id"],
            worker_type=worker_type,
            hostname=worker_info["hostname"],
            ip_address=worker_info["ip_address"],
            gpu_info=worker_info["gpu_info"],
            capabilities=worker_info["capabilities"],
            max_concurrent_tasks=worker_info.get("max_concurrent_tasks", 4),
            heartbeat_interval=worker_info.get("heartbeat_interval", 30)
        )
        
        # Register with worker manager
        success = await worker_manager.register_worker(worker_info_obj)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to register worker in the system"
            )
        
        # Start monitoring if not already running
        await worker_manager.start_monitoring()
        
        return {
            "message": "Worker registered successfully",
            "worker_id": worker_info_obj.worker_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error registering worker: {str(e)}"
        )


@router.post("/heartbeat/{worker_id}")
async def worker_heartbeat(
    worker_id: str,
    current_user: TokenData = Depends(verify_token)
):
    """Update worker heartbeat to show it's still alive"""
    try:
        success = await worker_manager.heartbeat(worker_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Worker not found or not registered"
            )
        
        return {
            "message": "Heartbeat received",
            "worker_id": worker_id,
            "timestamp": __import__('time').time()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing heartbeat: {str(e)}"
        )


@router.get("/status")
async def get_workers_status(
    current_user: TokenData = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get status of all registered workers"""
    try:
        # Get workers from database
        from sqlalchemy import select
        result = await db.execute(select(Worker))
        db_workers = result.scalars().all()
        
        # Get active workers from registry
        registry_workers = worker_manager.registry._workers
        
        workers_status = []
        for db_worker in db_workers:
            worker_status = {
                "id": db_worker.worker_id,
                "name": db_worker.name,
                "host": db_worker.host,
                "port": db_worker.port,
                "gpu_model": db_worker.gpu_model,
                "status": db_worker.status,
                "last_heartbeat": db_worker.last_heartbeat.isoformat() if db_worker.last_heartbeat else None,
                "capabilities": db_worker.capabilities,
                "is_active_in_registry": db_worker.worker_id in registry_workers,
                "active_tasks": worker_manager.registry.get_worker_load(db_worker.worker_id) if db_worker.worker_id in registry_workers else 0
            }
            workers_status.append(worker_status)
        
        return {
            "workers": workers_status,
            "total_count": len(workers_status),
            "active_count": len([w for w in workers_status if w["status"] == WorkerStatus.ACTIVE.value])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting workers status: {str(e)}"
        )


@router.get("/types")
async def get_worker_types(
    current_user: TokenData = Depends(verify_token)
):
    """Get available worker types"""
    return {
        "worker_types": [wtype.value for wtype in WorkerType]
    }


@router.post("/assign-task")
async def assign_task(
    task_request: Dict[str, Any],
    current_user: TokenData = Depends(verify_token)
):
    """Assign a task to an available worker"""
    try:
        # Validate required fields
        if "task_type" not in task_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing task_type in request"
            )
        
        if "task_data" not in task_request:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing task_data in request"
            )
        
        # Validate worker type
        try:
            worker_type = WorkerType(task_request["task_type"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid worker type. Must be one of: {[e.value for e in WorkerType]}"
            )
        
        # Assign task to available worker
        result = await worker_manager.assign_task(worker_type, task_request["task_data"])
        if not result:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No available workers for type: {task_request['task_type']}"
            )
        
        return {
            "message": "Task assigned successfully",
            "task_id": result["task_id"],
            "worker_id": result["worker_id"],
            "worker_hostname": result["worker_hostname"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error assigning task: {str(e)}"
        )


@router.get("/health")
async def workers_health_check():
    """Health check for worker management system"""
    try:
        # Check if worker manager is running
        is_monitoring = worker_manager._monitor_task is not None and not worker_manager._monitor_task.done()
        
        # Get basic stats
        total_workers = len(worker_manager.registry._workers)
        active_workers = len([w for w in worker_manager.registry._workers.values()])
        
        return {
            "status": "healthy",
            "is_monitoring_active": is_monitoring,
            "total_registered_workers": total_workers,
            "active_workers": active_workers,
            "timestamp": __import__('time').time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Worker health check failed: {str(e)}"
        )