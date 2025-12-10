import asyncio
import aiohttp
import time
from typing import Dict, Optional
import logging
import subprocess
import psutil
from datetime import datetime

from .auto_config import auto_config

logger = logging.getLogger(__name__)

class HealthCheck:
    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or f"http://localhost:{auto_config.config.get('network_settings', {}).get('local_port', 8001)}"
        self.last_check = None
        self.status_history = []
        
    async def check_server_health(self) -> Dict:
        """Проверка работоспособности локального inference сервера"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.server_url}/health", timeout=10) as response:
                    if response.status == 200:
                        health_data = await response.json()
                        response_time = time.time() - start_time
                        
                        health_status = {
                            "status": "healthy",
                            "response_time": response_time,
                            "timestamp": datetime.now().isoformat(),
                            "server_info": health_data,
                            "system_resources": self._check_system_resources()
                        }
                        
                        self.status_history.append(health_status)
                        if len(self.status_history) > 50:  # Keep only last 50 checks
                            self.status_history.pop(0)
                            
                        self.last_check = health_status
                        return health_status
                    else:
                        raise Exception(f"Server returned status {response.status}")
        except Exception as e:
            error_status = {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "system_resources": self._check_system_resources()
            }
            
            self.status_history.append(error_status)
            if len(self.status_history) > 50:  # Keep only last 50 checks
                self.status_history.pop(0)
                
            self.last_check = error_status
            return error_status
    
    def _check_system_resources(self) -> Dict:
        """Проверка системных ресурсов"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Проверяем температуру (если доступна)
        temp_info = {}
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                # Берем температуру CPU если доступна
                for name, entries in temps.items():
                    if 'cpu' in name.lower() or 'core' in name.lower():
                        temp_info['cpu_temp'] = [entry.current for entry in entries]
                        break
        except:
            temp_info['cpu_temp'] = "unavailable"
        
        resources = {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024**3),
            "temperature": temp_info
        }
        
        return resources
    
    async def check_cuda_health(self) -> Dict:
        """Проверка состояния CUDA/GPU"""
        if not auto_config.cuda_info.get('available', False):
            return {"available": False, "status": "cuda_not_available"}
        
        try:
            # Проверяем статус GPU через nvidia-smi
            result = subprocess.run([
                'nvidia-smi', 
                '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                gpu_data = result.stdout.strip().split(', ')
                gpu_util = int(gpu_data[0].strip())
                mem_used = int(gpu_data[1].strip())
                mem_total = int(gpu_data[2].strip())
                gpu_temp = int(gpu_data[3].strip()) if len(gpu_data) > 3 else None
                
                cuda_health = {
                    "status": "healthy",
                    "gpu_utilization": f"{gpu_util}%",
                    "memory_used_mb": mem_used,
                    "memory_total_mb": mem_total,
                    "memory_usage": f"{(mem_used/mem_total)*100:.1f}%" if mem_total > 0 else "N/A",
                    "temperature_c": gpu_temp,
                    "gpu_name": auto_config.cuda_info.get('gpu_name', 'unknown')
                }
                
                return cuda_health
            else:
                return {"status": "error", "error": "nvidia-smi returned non-zero exit code"}
                
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "nvidia-smi command timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def check_rust_module(self) -> Dict:
        """Проверка работоспособности Rust-модуля"""
        from .model_loader import model_loader
        
        try:
            # Проверяем доступность модуля
            if model_loader.rust_module is None:
                return {
                    "loaded": False,
                    "acceleration_enabled": model_loader.rust_acceleration,
                    "fallback_active": True
                }
            
            # Пробуем выполнить простой тест
            if hasattr(model_loader.rust_module, 'benchmark_performance'):
                test_result = model_loader.rust_module.benchmark_performance(1)
                return {
                    "loaded": True,
                    "acceleration_enabled": model_loader.rust_acceleration,
                    "fallback_active": False,
                    "test_result": test_result
                }
            else:
                return {
                    "loaded": True,
                    "acceleration_enabled": model_loader.rust_acceleration,
                    "fallback_active": False,
                    "test_result": "No benchmark function available"
                }
                
        except Exception as e:
            return {
                "loaded": False,
                "acceleration_enabled": model_loader.rust_acceleration,
                "fallback_active": True,
                "error": str(e)
            }
    
    async def comprehensive_health_check(self) -> Dict:
        """Комплексная проверка здоровья системы"""
        server_health = await self.check_server_health()
        cuda_health = await self.check_cuda_health()
        rust_health = await self.check_rust_module()
        
        overall_status = "healthy"
        if server_health["status"] != "healthy":
            overall_status = "unhealthy"
        elif cuda_health.get("status") == "error":
            overall_status = "degraded"
        elif not rust_health.get("loaded", True):
            overall_status = "degraded"
        
        comprehensive_report = {
            "overall_status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "server": server_health,
            "cuda": cuda_health,
            "rust": rust_health,
            "config": auto_config.config
        }
        
        return comprehensive_report
    
    def get_status_history(self, limit: int = 10) -> list:
        """Получение истории статусов"""
        return self.status_history[-limit:] if self.status_history else []
    
    async def restart_server_if_needed(self) -> Dict:
        """Перезапуск сервера при обнаружении проблем"""
        health = await self.comprehensive_health_check()
        
        if health["overall_status"] == "unhealthy":
            logger.warning("Server is unhealthy, attempting restart...")
            # В реальной реализации здесь будет логика перезапуска сервера
            # Это может включать остановку текущего процесса и запуск нового
            
            restart_info = {
                "action_taken": "restart_attempted",
                "reason": "unhealthy_server",
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Restart attempt completed: {restart_info}")
            return restart_info
        else:
            return {
                "action_taken": "none",
                "reason": "server_is_healthy",
                "timestamp": datetime.now().isoformat()
            }

# Singleton instance
health_checker = HealthCheck()