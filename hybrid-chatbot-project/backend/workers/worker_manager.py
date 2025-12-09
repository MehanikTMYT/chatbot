import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
import redis.asyncio as redis
from redis.asyncio.exceptions import ConnectionError

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..database.models import Worker, WorkerStatus, Task
from ..core.config import settings
from ..core.logging import logger

class WorkerType(Enum):
    LLM = "llm"
    WEB = "web"
    EMBEDDING = "embedding"

@dataclass
class WorkerInfo:
    worker_id: str
    worker_type: WorkerType
    hostname: str
    ip_address: str
    gpu_info: Dict[str, Any]
    capabilities: List[str]
    max_concurrent_tasks: int
    heartbeat_interval: int = 30

class WorkerRegistry:
    def __init__(self):
        self._workers: Dict[str, WorkerInfo] = {}
        self._last_heartbeat: Dict[str, datetime] = {}
        self._active_tasks: Dict[str, List[str]] = {}
        self._lock = asyncio.Lock()
        self._redis_client: Optional[redis.Redis] = None
        self._worker_discovery_channel = "worker_discovery"
        self._task_queue = "task_queue"
        self._dead_letter_queue = "dead_letter_queue"
    
    async def initialize_redis(self):
        """Initialize Redis connection"""
        try:
            self._redis_client = redis.from_url(settings.REDIS_URL)
            # Test connection
            await self._redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self._redis_client = None
    
    async def discover_workers(self) -> List[Dict[str, Any]]:
        """Discover workers in the local network via Redis pub/sub"""
        if not self._redis_client:
            return []
        
        try:
            # Publish discovery request
            await self._redis_client.publish(self._worker_discovery_channel, 
                                           json.dumps({
                                               "type": "discovery_request",
                                               "timestamp": datetime.utcnow().isoformat()
                                           }))
            
            # Wait briefly for responses
            await asyncio.sleep(1)
            
            # Get discovered workers from Redis
            discovered_workers = await self._redis_client.lrange("discovered_workers", 0, -1)
            return [json.loads(worker) for worker in discovered_workers]
        except Exception as e:
            logger.error(f"Error discovering workers: {e}")
            return []
    
    async def publish_worker_info(self):
        """Publish worker information to Redis for discovery"""
        if not self._redis_client:
            return
        
        try:
            for worker_id, worker_info in self._workers.items():
                worker_data = {
                    "worker_id": worker_id,
                    "worker_type": worker_info.worker_type.value,
                    "hostname": worker_info.hostname,
                    "ip_address": worker_info.ip_address,
                    "gpu_info": worker_info.gpu_info,
                    "capabilities": worker_info.capabilities,
                    "max_concurrent_tasks": worker_info.max_concurrent_tasks,
                    "timestamp": datetime.utcnow().isoformat()
                }
                await self._redis_client.publish(self._worker_discovery_channel,
                                               json.dumps({
                                                   "type": "worker_announcement",
                                                   "data": worker_data
                                               }))
        except Exception as e:
            logger.error(f"Error publishing worker info: {e}")
    
    async def register_worker(self, worker_info: WorkerInfo) -> bool:
        """Register a new worker in the system"""
        async with self._lock:
            try:
                self._workers[worker_info.worker_id] = worker_info
                self._last_heartbeat[worker_info.worker_id] = datetime.utcnow()
                self._active_tasks[worker_info.worker_id] = []
                
                # Save to database
                async with AsyncSession(settings.DB_ENGINE) as session:
                    # Check if worker already exists
                    result = await session.execute(
                        select(Worker).where(Worker.worker_id == worker_info.worker_id)
                    )
                    existing_worker = result.scalar_one_or_none()
                    
                    if existing_worker:
                        # Update existing worker
                        existing_worker.name = worker_info.worker_type.value
                        existing_worker.host = worker_info.ip_address
                        existing_worker.status = WorkerStatus.ACTIVE.value
                        existing_worker.last_heartbeat = datetime.utcnow()
                        existing_worker.capabilities = json.dumps(worker_info.capabilities)
                        existing_worker.gpu_model = worker_info.gpu_info.get('model', '')
                        existing_worker.gpu_memory = worker_info.gpu_info.get('memory_mb', 0)
                        existing_worker.total_memory = worker_info.gpu_info.get('total_memory_mb', 0)
                        existing_worker.cpu_count = worker_info.gpu_info.get('cpu_count', 0)
                        existing_worker.port = worker_info.gpu_info.get('port', 8000)
                    else:
                        # Create new worker
                        worker_db = Worker(
                            worker_id=worker_info.worker_id,
                            name=worker_info.worker_type.value,
                            host=worker_info.ip_address,
                            port=worker_info.gpu_info.get('port', 8000),
                            gpu_model=worker_info.gpu_info.get('model', ''),
                            gpu_memory=worker_info.gpu_info.get('memory_mb', 0),
                            total_memory=worker_info.gpu_info.get('total_memory_mb', 0),
                            cpu_count=worker_info.gpu_info.get('cpu_count', 0),
                            status=WorkerStatus.ACTIVE.value,
                            last_heartbeat=datetime.utcnow(),
                            capabilities=json.dumps(worker_info.capabilities),
                            performance_metrics={}
                        )
                        session.add(worker_db)
                    
                    await session.commit()
                
                logger.info(f"Worker {worker_info.worker_id} registered successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to register worker: {e}")
                return False
    
    async def heartbeat(self, worker_id: str) -> bool:
        """Update worker heartbeat timestamp"""
        async with self._lock:
            if worker_id not in self._workers:
                return False
            
            self._last_heartbeat[worker_id] = datetime.utcnow()
            
            # Update in database
            async with AsyncSession(settings.DB_ENGINE) as session:
                result = await session.execute(
                    select(Worker).where(Worker.worker_id == worker_id)
                )
                worker_db = result.scalar_one_or_none()
                if worker_db:
                    worker_db.last_heartbeat = datetime.utcnow()
                    worker_db.status = WorkerStatus.ACTIVE.value
                    await session.commit()
            
            return True
    
    async def unregister_worker(self, worker_id: str) -> bool:
        """Unregister a worker from the system"""
        async with self._lock:
            if worker_id in self._workers:
                del self._workers[worker_id]
                if worker_id in self._last_heartbeat:
                    del self._last_heartbeat[worker_id]
                if worker_id in self._active_tasks:
                    del self._active_tasks[worker_id]
                
                # Update in database
                async with AsyncSession(settings.DB_ENGINE) as session:
                    result = await session.execute(
                        select(Worker).where(Worker.worker_id == worker_id)
                    )
                    worker_db = result.scalar_one_or_none()
                    if worker_db:
                        worker_db.status = WorkerStatus.INACTIVE.value
                        await session.commit()
                
                logger.info(f"Worker {worker_id} unregistered")
                return True
            return False
    
    def get_workers_by_type(self, worker_type: WorkerType) -> List[WorkerInfo]:
        """Get all active workers of a specific type"""
        active_workers = []
        current_time = datetime.utcnow()
        
        for worker_id, worker_info in self._workers.items():
            # Check if heartbeat is recent (within 2 intervals)
            last_hb = self._last_heartbeat.get(worker_id, datetime.min)
            if current_time - last_hb < timedelta(seconds=worker_info.heartbeat_interval * 2):
                if worker_info.worker_type == worker_type:
                    active_workers.append(worker_info)
        
        return active_workers
    
    def get_worker(self, worker_id: str) -> Optional[WorkerInfo]:
        """Get specific worker by ID"""
        current_time = datetime.utcnow()
        last_hb = self._last_heartbeat.get(worker_id, datetime.min)
        
        # Check if heartbeat is recent
        if current_time - last_hb < timedelta(seconds=60):
            return self._workers.get(worker_id)
        return None
    
    def assign_task(self, worker_id: str, task_id: str) -> bool:
        """Assign a task to a worker"""
        if worker_id in self._active_tasks:
            self._active_tasks[worker_id].append(task_id)
            return True
        return False
    
    def complete_task(self, worker_id: str, task_id: str) -> bool:
        """Mark a task as completed for a worker"""
        if worker_id in self._active_tasks:
            if task_id in self._active_tasks[worker_id]:
                self._active_tasks[worker_id].remove(task_id)
                return True
        return False
    
    def get_worker_load(self, worker_id: str) -> int:
        """Get current load of a worker (number of active tasks)"""
        if worker_id in self._active_tasks:
            return len(self._active_tasks[worker_id])
        return 0
    
    async def cleanup_inactive_workers(self):
        """Remove workers that haven't sent heartbeat for too long"""
        async with self._lock:
            current_time = datetime.utcnow()
            workers_to_remove = []
            
            for worker_id, last_hb in self._last_heartbeat.items():
                if current_time - last_hb > timedelta(seconds=120):  # 2 minutes timeout
                    workers_to_remove.append(worker_id)
            
            for worker_id in workers_to_remove:
                await self.unregister_worker(worker_id)

class WorkerManager:
    def __init__(self):
        self.registry = WorkerRegistry()
        self._monitor_task: Optional[asyncio.Task] = None
        self._task_queue_monitor: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """Initialize the worker manager with Redis and other services"""
        await self.registry.initialize_redis()
    
    async def start_monitoring(self):
        """Start the worker monitoring background task"""
        if self._monitor_task is None or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_workers())
        
        # Start task queue monitoring
        if self._task_queue_monitor is None or self._task_queue_monitor.done():
            self._task_queue_monitor = asyncio.create_task(self._monitor_task_queue())
    
    async def stop_monitoring(self):
        """Stop the worker monitoring background task"""
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        if self._task_queue_monitor and not self._task_queue_monitor.done():
            self._task_queue_monitor.cancel()
            try:
                await self._task_queue_monitor
            except asyncio.CancelledError:
                pass
    
    async def _monitor_workers(self):
        """Background task to monitor worker health"""
        while True:
            try:
                await self.registry.cleanup_inactive_workers()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                logger.info("Worker monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in worker monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _monitor_task_queue(self):
        """Background task to monitor and process task queue"""
        while True:
            try:
                # Process tasks from Redis Streams
                if self.registry._redis_client:
                    # Process task queue using XREAD
                    try:
                        # Read pending tasks from the queue
                        results = await self.registry._redis_client.xread(
                            {self.registry._task_queue: "$"}, 
                            count=10, 
                            block=1000  # Wait 1 second for new messages
                        )
                        
                        if results:
                            for stream, messages in results:
                                for message_id, message_data in messages:
                                    task_data = json.loads(message_data[b'message'].decode('utf-8'))
                                    await self._process_task_from_queue(task_data, message_id)
                    except Exception as e:
                        logger.error(f"Error reading from task queue: {e}")
                
                await asyncio.sleep(1)  # Brief pause to prevent busy loop
            except asyncio.CancelledError:
                logger.info("Task queue monitoring task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in task queue monitoring: {e}")
                await asyncio.sleep(5)
    
    async def _process_task_from_queue(self, task_data: Dict[str, Any], message_id: str):
        """Process a task from the Redis queue"""
        try:
            # Determine worker type from task
            worker_type_str = task_data.get("task_type", "llm")
            try:
                worker_type = WorkerType(worker_type_str)
            except ValueError:
                logger.error(f"Invalid worker type in task: {worker_type_str}")
                # Move to dead letter queue
                if self.registry._redis_client:
                    await self.registry._redis_client.xadd(
                        self.registry._dead_letter_queue,
                        {"message": json.dumps(task_data)}
                    )
                return
            
            # Find available worker
            worker = await self.get_available_worker(worker_type)
            if not worker:
                logger.warning(f"No available workers for task type {worker_type_str}, requeuing")
                # Requeue with a delay
                await asyncio.sleep(5)
                return
            
            # Assign task to worker
            task_id = task_data.get("task_id", str(uuid.uuid4()))
            self.registry.assign_task(worker.worker_id, task_id)
            
            # Send task to worker (this would be implemented based on your worker communication method)
            # For now, we'll just log it
            logger.info(f"Assigned task {task_id} to worker {worker.worker_id}")
            
        except Exception as e:
            logger.error(f"Error processing task from queue: {e}")
            # Move to dead letter queue
            if self.registry._redis_client:
                await self.registry._redis_client.xadd(
                    self.registry._dead_letter_queue,
                    {"message": json.dumps(task_data)}
                )
    
    async def register_worker(self, worker_info: WorkerInfo) -> bool:
        """Register a new worker"""
        result = await self.registry.register_worker(worker_info)
        if result:
            # Publish worker info for discovery
            await self.registry.publish_worker_info()
        return result
    
    async def heartbeat(self, worker_id: str) -> bool:
        """Handle worker heartbeat"""
        return await self.registry.heartbeat(worker_id)
    
    async def get_available_worker(self, worker_type: WorkerType) -> Optional[WorkerInfo]:
        """Get an available worker of specified type with lowest load"""
        workers = self.registry.get_workers_by_type(worker_type)
        available_worker = None
        min_load = float('inf')
        
        for worker in workers:
            load = self.registry.get_worker_load(worker.worker_id)
            if load < worker.max_concurrent_tasks and load < min_load:
                min_load = load
                available_worker = worker
        
        return available_worker
    
    async def assign_task(self, worker_type: WorkerType, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Assign a task to an available worker"""
        # Add task to Redis queue with priority
        priority = task_data.get("priority", 0)
        task_id = str(uuid.uuid4())
        
        task_payload = {
            "task_id": task_id,
            "task_type": worker_type.value,
            "task_data": task_data,
            "priority": priority,
            "created_at": datetime.utcnow().isoformat(),
            "assigned_worker_id": None
        }
        
        if self.registry._redis_client:
            try:
                # Add to Redis stream with priority
                await self.registry._redis_client.xadd(
                    self.registry._task_queue,
                    {"message": json.dumps(task_payload)},
                    maxlen=10000  # Limit stream size
                )
                
                # For immediate processing if workers are available
                worker = await self.get_available_worker(worker_type)
                if worker:
                    # Direct assignment if worker is available
                    self.registry.assign_task(worker.worker_id, task_id)
                    
                    result = {
                        "task_id": task_id,
                        "worker_id": worker.worker_id,
                        "worker_hostname": worker.hostname,
                        "task_data": task_data,
                        "queue_status": "processed_immediately"
                    }
                    return result
                else:
                    # Task queued for later processing
                    result = {
                        "task_id": task_id,
                        "task_data": task_data,
                        "queue_status": "queued_waiting"
                    }
                    return result
            except Exception as e:
                logger.error(f"Error queuing task in Redis: {e}")
                # Fallback to direct assignment
                worker = await self.get_available_worker(worker_type)
                if not worker:
                    logger.warning(f"No available workers for type {worker_type}")
                    return None
                
                self.registry.assign_task(worker.worker_id, task_id)
                
                result = {
                    "task_id": task_id,
                    "worker_id": worker.worker_id,
                    "worker_hostname": worker.hostname,
                    "task_data": task_data,
                    "queue_status": "direct_assignment"
                }
                
                return result
        else:
            # Fallback to direct assignment if Redis is not available
            worker = await self.get_available_worker(worker_type)
            if not worker:
                logger.warning(f"No available workers for type {worker_type}")
                return None
            
            task_id = str(uuid.uuid4())
            self.registry.assign_task(worker.worker_id, task_id)
            
            result = {
                "task_id": task_id,
                "worker_id": worker.worker_id,
                "worker_hostname": worker.hostname,
                "task_data": task_data,
                "queue_status": "direct_assignment_no_redis"
            }
            
            return result

# Global worker manager instance
worker_manager = WorkerManager()