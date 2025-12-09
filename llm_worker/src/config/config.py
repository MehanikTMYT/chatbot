"""
Configuration module for LLM Worker
Contains settings for TensorRT optimization and RTX 4070 specific parameters
"""
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelConfig:
    """Model-specific configuration"""
    # Model identification
    model_name: str = "Qwen3-8B-Q5_K_M"
    model_path: str = "models/Qwen3-8B-Q5_K_M"
    tensorrt_model_path: str = "models/trt_models/Qwen3-8B-Q5_K_M.plan"
    tokenizer_path: str = "models/Qwen3-8B-Q5_K_M"
    
    # Quantization settings
    quantization_type: str = "int8"  # Options: "fp16", "int8", "int4"
    smooth_quant: bool = True
    per_channel_quant: bool = True
    
    # Model architecture parameters
    hidden_size: int = 4096
    num_attention_heads: int = 32
    num_key_value_heads: int = 32
    intermediate_size: int = 14336
    num_hidden_layers: int = 32

@dataclass
class HardwareConfig:
    """Hardware-specific configuration for RTX 4070"""
    # GPU settings
    gpu_device_id: int = 0
    gpu_memory_fraction: float = 0.85  # Use 85% of available GPU memory
    max_batch_size: int = 4
    max_workspace_size: int = 2 * 1024 * 1024 * 1024  # 2GB workspace
    
    # RTX 4070 specific optimizations
    enable_fp16: bool = True  # RTX 4070 has good FP16 performance
    enable_int8: bool = True  # Enable INT8 quantization
    use_cublas_lt: bool = True  # Use cuBLASLt for better performance
    
    # Memory management
    gpu_memory_limit: int = 14 * 1024 * 1024 * 1024  # 14GB limit for RTX 4070
    cpu_offload_enabled: bool = False  # Disable CPU offload for better performance

@dataclass
class PerformanceConfig:
    """Performance-related configuration"""
    # Generation settings
    max_new_tokens: int = 1024
    min_new_tokens: int = 1
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    repetition_penalty: float = 1.1
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    
    # Performance targets
    target_generation_time: float = 3.0  # Target <3 seconds for 1024 tokens
    target_tokens_per_second: int = 200  # >200 tokens/sec
    
    # Parallelism settings
    num_decoding_streams: int = 2
    max_beam_width: int = 1
    enable_chunked_context: bool = True

@dataclass
class SystemConfig:
    """System-level configuration"""
    # Paths
    models_dir: str = "models/"
    cache_dir: str = "cache/"
    logs_dir: str = "logs/"
    temp_dir: str = "temp/"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # API settings
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    max_concurrent_requests: int = 10
    request_timeout: int = 120  # 2 minutes timeout
    
    # Safety settings
    max_prompt_length: int = 4096
    max_total_tokens: int = 8192
    enable_prompt_validation: bool = True
    enable_output_validation: bool = True

@dataclass
class LLMWorkerConfig:
    """Main configuration for the LLM Worker"""
    model_config: ModelConfig = None
    hardware_config: HardwareConfig = None
    performance_config: PerformanceConfig = None
    system_config: SystemConfig = None
    
    def __post_init__(self):
        if self.model_config is None:
            self.model_config = ModelConfig()
        if self.hardware_config is None:
            self.hardware_config = HardwareConfig()
        if self.performance_config is None:
            self.performance_config = PerformanceConfig()
        if self.system_config is None:
            self.system_config = SystemConfig()
    
    @classmethod
    def from_file(cls, config_path: str) -> 'LLMWorkerConfig':
        """Load configuration from JSON file"""
        import json
        
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create configuration objects from loaded data
        model_cfg = ModelConfig(**data.get('model_config', {}))
        hw_cfg = HardwareConfig(**data.get('hardware_config', {}))
        perf_cfg = PerformanceConfig(**data.get('performance_config', {}))
        sys_cfg = SystemConfig(**data.get('system_config', {}))
        
        return cls(
            model_config=model_cfg,
            hardware_config=hw_cfg,
            performance_config=perf_cfg,
            system_config=sys_cfg
        )
    
    def to_file(self, config_path: str):
        """Save configuration to JSON file"""
        import json
        
        # Convert to dictionary
        config_dict = {
            'model_config': self.model_config.__dict__,
            'hardware_config': self.hardware_config.__dict__,
            'performance_config': self.performance_config.__dict__,
            'system_config': self.system_config.__dict__
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

def get_default_config() -> LLMWorkerConfig:
    """Get default configuration optimized for RTX 4070"""
    return LLMWorkerConfig()

# Default configuration instance
default_config = get_default_config()