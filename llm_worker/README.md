# LLM Worker for Windows 11 with TensorRT Optimization

High-performance LLM worker optimized for NVIDIA RTX 4070 on Windows 11, featuring TensorRT optimization for Qwen3-8B-Q5_K_M model.

## Features

- **TensorRT Optimization**: Full optimization for RTX 4070 with INT8/FP16 quantization
- **High Performance**: Target <3 seconds for 1024 token generation
- **Resource Management**: Intelligent GPU memory management and monitoring
- **API Server**: FastAPI-based REST API with streaming support
- **Health Monitoring**: Comprehensive system and GPU monitoring with auto-recovery
- **Windows 11 Support**: Full compatibility with Windows 11 APIs and paths

## Requirements

### Hardware
- NVIDIA RTX 4070 (12GB VRAM) or better
- At least 32GB system RAM
- 20GB+ free disk space for models

### Software
- Windows 11 (64-bit)
- Python 3.9 or higher
- NVIDIA GPU Drivers 545+ 
- CUDA 12.1
- TensorRT 8.6

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install NVIDIA Components

For Windows 11, install:
- [NVIDIA GPU Drivers](https://www.nvidia.com/drivers/) (545+)
- [CUDA Toolkit 12.1](https://developer.nvidia.com/cuda-12-1-0-download-archive)
- [TensorRT 8.6](https://developer.nvidia.com/tensorrt)

### 3. Install TensorRT-LLM

```bash
pip install tensorrt-llm
```

## Model Conversion

### 1. Download Qwen3-8B-Q5_K_M Model

```bash
# Download the model from Hugging Face
python src/python/model_converter.py --download --model_name "Qwen/Qwen2-7B-Instruct" --model_path "./models/Qwen2-7B-Instruct"
```

### 2. Convert to TensorRT Format

```bash
# Convert the model to TensorRT format optimized for RTX 4070
python src/python/tensorrt_converter.py \
  --model_path "./models/Qwen2-7B-Instruct" \
  --output_dir "./models/trt_models/Qwen2-7B-Instruct" \
  --precision float16 \
  --quantization weight_only_int8 \
  --max_batch_size 4
```

## Configuration

The system uses a configuration file to manage settings. Create a `config.json`:

```json
{
  "model_config": {
    "model_name": "Qwen3-8B-Q5_K_M",
    "model_path": "models/Qwen3-8B-Q5_K_M",
    "tensorrt_model_path": "models/trt_models/Qwen3-8B-Q5_K_M.plan",
    "tokenizer_path": "models/Qwen3-8B-Q5_K_M"
  },
  "hardware_config": {
    "gpu_device_id": 0,
    "gpu_memory_fraction": 0.85,
    "max_batch_size": 4,
    "enable_fp16": true,
    "enable_int8": true,
    "gpu_memory_limit": 14745600000
  },
  "performance_config": {
    "max_new_tokens": 1024,
    "target_generation_time": 3.0,
    "target_tokens_per_second": 200
  },
  "system_config": {
    "api_host": "127.0.0.1",
    "api_port": 8000,
    "log_level": "INFO"
  }
}
```

## Running the LLM Worker

### 1. Start the Service

```bash
python main.py --config config.json
```

### 2. Or with command line arguments

```bash
python main.py \
  --model-path "./models/trt_models/Qwen3-8B-Q5_K_M.plan" \
  --tokenizer-path "./models/Qwen3-8B-Q5_K_M" \
  --api-host 127.0.0.1 \
  --api-port 8000
```

## API Endpoints

### Health Check
```
GET /
GET /health
```

### Text Generation
```
POST /generate
Content-Type: application/json

{
  "prompt": "Write a story about AI",
  "max_new_tokens": 1024,
  "temperature": 0.7,
  "top_p": 0.9,
  "stream": false
}
```

### Streaming Generation
```
POST /generate_stream
Content-Type: application/json

{
  "prompt": "Write a poem",
  "max_new_tokens": 512,
  "temperature": 0.8
}
```

### Get Statistics
```
GET /stats
```

## Performance Targets

- Generation time: <3 seconds for 1024 tokens
- GPU memory usage: <16GB during inference
- Concurrent requests: 4+ simultaneous
- Tokens per second: >200
- Model load time: <30 seconds

## Monitoring and Health Checks

The system includes comprehensive monitoring:

- GPU utilization and memory
- System resources (CPU, RAM, disk)
- Generation performance metrics
- Automatic recovery from failures
- Health check endpoints

## Windows 11 Specific Optimizations

- Proper handling of Windows paths
- Compatibility with Windows security features
- Efficient use of Windows memory management
- Proper cleanup on shutdown

## Troubleshooting

### Common Issues

1. **CUDA not found**: Ensure CUDA 12.1 is properly installed and in PATH
2. **TensorRT not found**: Install TensorRT and verify installation
3. **GPU memory errors**: Reduce batch size or max tokens in config
4. **Model conversion fails**: Check model format compatibility

### Logs

Check logs in the configured logs directory for detailed error information.

## Development

### Project Structure
```
llm_worker/
├── src/
│   ├── python/          # Python source code
│   ├── rust/           # Rust components (future)
│   ├── config/         # Configuration files
│   ├── utils/          # Utility functions
│   └── api/            # API components
├── models/             # Model files
├── requirements.txt    # Python dependencies
├── main.py             # Main entry point
└── README.md          # This file
```

### Testing

Unit tests and integration tests are planned for future implementation.

## License

This project is licensed under the MIT License.