"""
Demo script for LLM Worker
Demonstrates the functionality of the LLM worker system
"""
import sys
import os
import asyncio
import json
from pathlib import Path

# Add the project root and src directories to the path
project_root = Path(__file__).parent
src_python = project_root / "src" / "python"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_python))

def demo_config():
    """Demonstrate configuration system"""
    print("=== Configuration Demo ===")
    
    from src.config.config import get_default_config, LLMWorkerConfig
    
    # Get default configuration
    config = get_default_config()
    print(f"Model: {config.model_config.model_name}")
    print(f"TensorRT path: {config.model_config.tensorrt_model_path}")
    print(f"Target generation time: {config.performance_config.target_generation_time}s")
    print(f"Max batch size: {config.hardware_config.max_batch_size}")
    
    # Show a serialized version
    config_dict = {
        'model_config': config.model_config.__dict__,
        'hardware_config': config.hardware_config.__dict__,
        'performance_config': config.performance_config.__dict__,
    }
    
    print(f"Sample config preview: {json.dumps(config_dict, indent=2)[:200]}...")
    print()

def demo_worker_structure():
    """Demonstrate LLM worker structure"""
    print("=== LLM Worker Structure Demo ===")
    
    from src.python.llm_worker import LLMWorker, GenerationConfig, RequestQueue, GPUManager
    
    # Show the structure without initializing actual model (to avoid CUDA dependencies)
    print("LLM Worker components:")
    print("- RequestQueue: Manages incoming requests with priority")
    print("- GPUManager: Handles GPU memory allocation and limits")
    print("- GenerationConfig: Controls generation parameters")
    
    # Create a sample request
    queue = RequestQueue()
    print(f"Created request queue, initial size: {queue.size()}")
    
    # Create sample generation config
    gen_config = GenerationConfig(
        max_new_tokens=512,
        temperature=0.7,
        top_p=0.9
    )
    print(f"Sample generation config: max_tokens={gen_config.max_new_tokens}, temp={gen_config.temperature}")
    
    # Show GPU manager (simulated)
    gpu_manager = GPUManager()
    print(f"GPU memory limit: {gpu_manager.max_memory / (1024**3):.1f} GB")
    print()

def demo_api_structure():
    """Demonstrate API structure"""
    print("=== API Structure Demo ===")
    
    print("API Endpoints:")
    print("GET  /              - Root endpoint")
    print("GET  /health        - Health check")
    print("POST /generate      - Text generation")
    print("POST /generate_stream - Streaming generation")
    print("GET  /stats         - Performance statistics")
    print("GET  /queue         - Queue status")
    print()
    
    # Show sample request/response structure
    sample_request = {
        "prompt": "Explain quantum computing in simple terms",
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.9,
        "stream": False
    }
    
    print(f"Sample request: {json.dumps(sample_request, indent=2)}")
    print()

def demo_monitoring():
    """Demonstrate monitoring capabilities"""
    print("=== Monitoring Demo ===")
    
    from src.python.monitoring import ResourceMonitor, HealthChecker
    
    print("Monitoring components:")
    print("- ResourceMonitor: Tracks GPU and system resources")
    print("- HealthChecker: Performs comprehensive system checks")
    print("- AutoRecoveryManager: Handles automatic recovery from failures")
    
    # Create monitoring instances
    monitor = ResourceMonitor()
    checker = HealthChecker()
    
    print(f"Monitor initialized: {type(monitor).__name__}")
    print(f"Checker initialized: {type(checker).__name__}")
    print()

def demo_conversion_pipeline():
    """Demonstrate model conversion pipeline"""
    print("=== Model Conversion Pipeline ===")
    
    print("Model conversion workflow:")
    print("1. Download Qwen3-8B-Q5_K_M model from Hugging Face")
    print("2. Apply RTX 4070 specific optimizations")
    print("3. Convert to TensorRT format with quantization")
    print("4. Optimize for FP16/INT8 precision")
    print("5. Generate TensorRT engine for fast inference")
    
    print("\nConversion command example:")
    print("python src/python/tensorrt_converter.py \\")
    print("  --model_path './models/Qwen3-8B-Q5_K_M' \\")
    print("  --output_dir './models/trt_models/Qwen3-8B-Q5_K_M' \\")
    print("  --precision float16 \\")
    print("  --quantization weight_only_int8 \\")
    print("  --max_batch_size 4")
    print()

def main():
    """Run all demos"""
    print("LLM Worker for Windows 11 with TensorRT Optimization - Demo")
    print("=" * 60)
    
    demo_config()
    demo_worker_structure()
    demo_api_structure()
    demo_monitoring()
    demo_conversion_pipeline()
    
    print("=" * 60)
    print("Demo completed! This demonstrates the structure and functionality")
    print("of the LLM worker system optimized for RTX 4070 on Windows 11.")
    print()
    print("Key features implemented:")
    print("- TensorRT optimization for high-performance inference")
    print("- GPU memory management with RTX 4070-specific settings")
    print("- Asynchronous request handling with priority queuing")
    print("- Comprehensive monitoring and health checks")
    print("- Auto-recovery from failures")
    print("- REST API with streaming support")
    print("- Configurable performance parameters")

if __name__ == "__main__":
    main()