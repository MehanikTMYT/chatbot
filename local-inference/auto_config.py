import os
import platform
import subprocess
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AutoConfig:
    def __init__(self):
        self.config = {}
        self.hardware_info = {}
        self.cuda_info = {}
        
    def detect_hardware(self) -> Dict:
        """Определение характеристик оборудования"""
        import psutil
        
        self.hardware_info = {
            'system': platform.system(),
            'node': platform.node(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total': psutil.virtual_memory().total,
            'memory_available': psutil.virtual_memory().available,
            'architecture': platform.architecture()[0]
        }
        
        logger.info(f"Detected hardware: {self.hardware_info['system']} {self.hardware_info['machine']}")
        logger.info(f"CPU cores: {self.hardware_info['cpu_count']} ({self.hardware_info['cpu_count_logical']} logical)")
        logger.info(f"Total memory: {self.hardware_info['memory_total'] / (1024**3):.2f} GB")
        
        return self.hardware_info
    
    def detect_cuda(self) -> Dict:
        """Определение CUDA и архитектуры GPU"""
        try:
            # Проверяем наличие nvidia-smi
            result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total,driver_version', 
                                   '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                gpu_info = result.stdout.strip().split('\n')[0].split(', ')
                gpu_name = gpu_info[0]
                
                # Определяем архитектуру CUDA для RTX 4070
                if 'RTX 4070' in gpu_name or '4070' in gpu_name:
                    cuda_arch = 'sm_89'  # Ada Lovelace architecture
                elif 'RTX 40' in gpu_name:
                    cuda_arch = 'sm_89'
                elif 'RTX 30' in gpu_name:
                    cuda_arch = 'sm_86'  # Ampere architecture
                elif 'RTX 20' in gpu_name or 'GTX 16' in gpu_name:
                    cuda_arch = 'sm_75'  # Turing architecture
                else:
                    cuda_arch = 'sm_50'  # Default fallback
                
                self.cuda_info = {
                    'available': True,
                    'gpu_name': gpu_name,
                    'memory_mb': int(gpu_info[1]),
                    'driver_version': gpu_info[2] if len(gpu_info) > 2 else 'unknown',
                    'cuda_arch': cuda_arch
                }
                
                logger.info(f"CUDA detected: {gpu_name}, Memory: {gpu_info[1]}MB, Arch: {cuda_arch}")
            else:
                self.cuda_info = {
                    'available': False,
                    'gpu_name': 'None',
                    'memory_mb': 0,
                    'driver_version': 'N/A',
                    'cuda_arch': 'cpu'
                }
                logger.info("CUDA not available")
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.cuda_info = {
                'available': False,
                'gpu_name': 'None',
                'memory_mb': 0,
                'driver_version': 'N/A',
                'cuda_arch': 'cpu'
            }
            logger.info("CUDA not available or nvidia-smi not found")
        
        return self.cuda_info
    
    def generate_config(self) -> Dict:
        """Генерация конфигурации на основе обнаруженного оборудования"""
        # Определяем оборудование
        self.detect_hardware()
        self.detect_cuda()
        
        # Генерируем конфигурацию
        self.config = {
            'hardware': self.hardware_info,
            'cuda': self.cuda_info,
            'inference_settings': {
                'use_gpu': self.cuda_info['available'],
                'cuda_arch': self.cuda_info.get('cuda_arch', 'cpu'),
                'max_memory_usage': int(self.hardware_info['memory_total'] * 0.8),  # 80% of total RAM
                'num_threads': max(1, self.hardware_info['cpu_count'] // 2),  # Use half of CPU cores
                'batch_size': 1 if not self.cuda_info['available'] else 4  # Smaller batch on CPU
            },
            'network_settings': {
                'local_port': int(os.getenv('LOCAL_INFERENCE_PORT', '8001')),
                'host': '0.0.0.0',  # Listen on all interfaces
                'timeout': int(os.getenv('INFERENCE_TIMEOUT', '120'))
            },
            'rust_settings': {
                'acceleration_enabled': os.getenv('RUST_ACCELERATION', 'true').lower() == 'true',
                'cuda_architecture': os.getenv('RUST_CUDA_ARCH', self.cuda_info.get('cuda_arch', 'cpu')),
                'fallback_on_error': os.getenv('RUST_FALLBACK_ON_ERROR', 'true').lower() == 'true'
            }
        }
        
        logger.info(f"Generated configuration for {'GPU' if self.cuda_info['available'] else 'CPU'} inference")
        
        return self.config
    
    def save_config(self, filepath: str = 'local_config.json'):
        """Сохранение конфигурации в файл"""
        if not self.config:
            self.generate_config()
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Configuration saved to {filepath}")
    
    def load_config(self, filepath: str = 'local_config.json') -> Dict:
        """Загрузка конфигурации из файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"Configuration loaded from {filepath}")
            return self.config
        except FileNotFoundError:
            logger.warning(f"Configuration file {filepath} not found, generating new one")
            return self.generate_config()
    
    @staticmethod
    def get_optimal_batch_size(cuda_available: bool, memory_gb: float) -> int:
        """Определение оптимального размера батча на основе доступной памяти"""
        if not cuda_available:
            return 1  # CPU inference - small batch
        
        # For RTX 4070 (12GB VRAM), we can use larger batches
        if memory_gb >= 10:
            return 8
        elif memory_gb >= 8:
            return 4
        elif memory_gb >= 6:
            return 2
        else:
            return 1

# Singleton instance
auto_config = AutoConfig()