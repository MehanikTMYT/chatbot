# Comprehensive System Architecture: Hybrid Chatbot with RTX 4070 Optimization

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Backend Implementation](#backend-implementation)
4. [LLM Worker Implementation](#llm-worker-implementation)
5. [Rust Components](#rust-components)
6. [Testing Strategies](#testing-strategies)
7. [Installation Guide](#installation-guide)
8. [Performance Optimizations](#performance-optimizations)

## System Overview

The hybrid chatbot system is a distributed architecture designed to leverage local computational resources (NVIDIA RTX 4070 GPUs on Windows 11) for high-performance LLM inference while maintaining a centralized API gateway, frontend, and database on a VDS server.

### Key Features:
- Distributed architecture with clear separation of concerns
- TensorRT optimization for RTX 4070 GPUs
- End-to-end encryption using Rust cryptography
- Real-time WebSocket communication
- Vector memory with semantic search capabilities
- Privacy-focused design with no external subscriptions required

## Architecture Components

### 1. VDS Server Components
- **API Gateway (FastAPI)**: Centralized entry point handling authentication, routing, and orchestration
- **Frontend (Vue 3 + Vite)**: Modern web interface with real-time chat capabilities
- **Database (MySQL)**: Persistent storage for conversations, messages, and user data
- **Cache (Redis)**: Session management and temporary data caching
- **Worker Management**: Registration, monitoring, and task assignment for computational workers

### 2. Local Worker Components (Windows 11)
- **LLM Worker**: TensorRT-optimized inference engine for LLM processing
- **Web Worker**: Web search and information retrieval capabilities
- **Secure Tunneling**: Encrypted communication with VDS server

## Backend Implementation

### API Gateway (FastAPI)

The backend implements a robust API gateway with the following key components:

#### Authentication and Authorization
- JWT-based token system with configurable expiration
- Role-based access control (user, admin, worker)
- Secure password hashing using bcrypt
- Rate limiting to prevent abuse

#### WebSocket Communication
- Real-time chat messaging with proper error handling
- Connection management with heartbeat mechanisms
- Message broadcasting to connected clients
- Proper cleanup of disconnected connections

#### Worker Management
- Dynamic worker registration and discovery
- Load balancing across available workers
- Health monitoring and automatic failover
- Task assignment with priority queuing

#### Database Models
- User management with proper relationships
- Conversation history with character associations
- Message storage with metadata support
- Worker status tracking with performance metrics
- Vector storage metadata for semantic search

### Example Implementation: Worker Assignment Logic
```python
async def assign_task(self, worker_type: WorkerType, task_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Assign a task to an available worker"""
    worker = await self.get_available_worker(worker_type)
    if not worker:
        logger.warning(f"No available workers for type {worker_type}")
        return None
    
    task_id = str(uuid.uuid4())
    self.registry.assign_task(worker.worker_id, task_id)
    
    # Send task to worker via HTTP API
    worker_url = f"http://{worker.ip_address}:{worker.gpu_info.get('port', 8000)}/generate"
    
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                worker_url,
                json={
                    "prompt": task_data.get("prompt", ""),
                    "max_new_tokens": task_data.get("max_new_tokens", 512),
                    "temperature": task_data.get("temperature", 0.7),
                    "top_p": task_data.get("top_p", 0.9),
                    "top_k": task_data.get("top_k", 50),
                    "repetition_penalty": task_data.get("repetition_penalty", 1.1),
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result_data = response.json()
                # Complete the task in registry
                self.registry.complete_task(worker.worker_id, task_id)
                
                result = {
                    "task_id": task_id,
                    "worker_id": worker.worker_id,
                    "worker_hostname": worker.hostname,
                    "result": result_data,
                    "status": "completed"
                }
            else:
                # Mark task as failed
                self.registry.complete_task(worker.worker_id, task_id)
                result = {
                    "task_id": task_id,
                    "worker_id": worker.worker_id,
                    "worker_hostname": worker.hostname,
                    "error": f"Worker returned status {response.status_code}",
                    "status": "failed"
                }
    except Exception as e:
        # Mark task as failed
        self.registry.complete_task(worker.worker_id, task_id)
        result = {
            "task_id": task_id,
            "worker_id": worker.worker_id,
            "worker_hostname": worker.hostname,
            "error": str(e),
            "status": "failed"
        }
    
    return result
```

## LLM Worker Implementation

### TensorRT Integration

The LLM worker implements full TensorRT optimization for RTX 4070 GPUs:

#### TensorRT Engine Loading
- Proper CUDA memory allocation for input/output bindings
- Stream-based execution for optimal performance
- Dynamic shape configuration for variable-length inputs
- Memory management to prevent GPU memory exhaustion

#### Inference Pipeline
- Tokenization using HuggingFace transformers
- CUDA memory transfer for input/output data
- Asynchronous execution for concurrent requests
- Proper error handling and resource cleanup

### Example Implementation: TensorRT Inference
```python
def generate(self, prompt: str, config: GenerationConfig) -> str:
    """Generate text using TensorRT engine"""
    try:
        # Tokenize input
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to('cuda')
        
        # Check GPU memory before generation
        estimated_memory = inputs.numel() * 4 * 1024  # Rough estimate
        
        if not self.gpu_manager.can_allocate(estimated_memory):
            logger.warning("Insufficient GPU memory, attempting to clear cache")
            torch.cuda.empty_cache()
        
        # Allocate memory for input on GPU
        input_ids = inputs[0].cpu().numpy()
        input_size = input_ids.nbytes
        
        # Copy input to GPU buffer
        cuda.memcpy_htod(self.input_buffer, input_ids)
        
        # Set input binding
        self.context.set_binding_shape(self.input_binding_index, input_ids.shape)
        
        # Perform inference
        start_time = time.time()
        
        # Execute the model
        success = self.context.execute_async_v2(
            bindings=[int(self.input_buffer), int(self.output_buffer)],
            stream_handle=self.stream.handle
        )
        
        if not success:
            raise RuntimeError("TensorRT inference execution failed")
        
        # Synchronize the stream
        self.stream.synchronize()
        
        # Copy output from GPU to CPU
        output_size = self.output_shape[0] * self.output_shape[1] * 4  # 4 bytes per int32
        output_data = np.empty(self.output_shape[0] * self.output_shape[1], dtype=np.int32)
        cuda.memcpy_dtoh(output_data, self.output_buffer)
        
        # Reshape and decode output
        output_data = output_data.reshape(self.output_shape)
        output_tokens = output_data[0]  # Get first batch
        
        # Remove padding zeros and decode
        output_tokens = output_tokens[output_tokens != 0]
        generated_text = self.tokenizer.decode(output_tokens, skip_special_tokens=True)
        
        end_time = time.time()
        logger.info(f"Generated {len(output_tokens)} tokens in {end_time - start_time:.2f}s")
        
        return generated_text
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise
```

### Resource Management
- GPU memory allocation tracking
- Concurrent request handling with thread pool
- Automatic memory cleanup
- Performance monitoring and metrics collection

## Rust Components

### Cryptographic Implementation

The Rust crypto module provides secure communication with the following features:

#### AEAD Encryption
- AES-256-GCM and ChaCha20-Poly1305 algorithms
- Random nonce generation for each encryption
- Proper authentication tag handling
- Secure random number generation using system entropy

#### Example Implementation: Encryption
```rust
/// Encrypts data using the configured algorithm
pub fn encrypt(&self, data: &[u8]) -> Result<EncryptedMessage> {
    let key_bytes = &self.config.key;
    let alg = match self.config.algorithm {
        CryptoAlgorithm::Aes256Gcm => &aead::AES_256_GCM,
        CryptoAlgorithm::ChaCha20Poly1305 => &aead::CHACHA20_POLY1305,
    };
    
    let unbound_key = UnboundKey::new(alg, key_bytes)?;
    let key = LessSafeKey::new(unbound_key);
    
    // Generate random nonce (IV)
    let mut nonce_bytes = [0u8; 12];  // 96-bit nonce for AES-GCM
    get_random_bytes(&mut nonce_bytes);
    let nonce = Nonce::try_assume_unique_for_key(nonce_bytes)?;
    
    // Create additional authenticated data (AAD)
    let aad = Aad::from(&[]);
    
    // Prepare buffer for encryption (data + tag)
    let mut in_out = data.to_vec();
    let tag = key.seal_in_place_append_tag(nonce, aad, &mut in_out)?;
    
    Ok(EncryptedMessage {
        data: in_out,
        iv: nonce_bytes.to_vec(),
        tag: Some(tag.as_ref().to_vec()),
        timestamp: std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_secs(),
    })
}
```

### TensorRT Bindings

The Rust tensorrt module provides high-performance bindings for TensorRT integration:
- Low-level CUDA interoperability
- Memory management for GPU tensors
- Optimized inference execution
- Error handling and validation

## Testing Strategies

### White Box Testing

White box testing focuses on internal structures and implementation details:

#### 1. Unit Tests
- Test individual functions and methods
- Test edge cases and error conditions
- Test data validation and sanitization
- Test memory management and resource cleanup

#### 2. Integration Tests
- Test component interactions
- Test API endpoints with various inputs
- Test database operations
- Test worker communication

#### 3. Code Coverage
- Aim for 80%+ line coverage
- Focus on critical paths and error conditions
- Use tools like pytest-cov for analysis

#### 4. Memory Leak Detection
- Monitor memory usage during long-running operations
- Test garbage collection effectiveness
- Validate resource cleanup in all code paths

### Black Box Testing

Black box testing focuses on functionality without knowledge of internal implementation:

#### 1. Functional Testing
- Test all API endpoints
- Validate input/output formats
- Test authentication and authorization
- Test error handling and responses

#### 2. Performance Testing
- Load testing with multiple concurrent users
- Response time measurements
- Throughput analysis
- Resource utilization monitoring

#### 3. Security Testing
- Input validation testing
- Authentication bypass attempts
- Authorization checks
- Data sanitization verification

#### 4. End-to-End Testing
- Complete user workflow testing
- Cross-component integration testing
- Real-world scenario testing

### Testing Commands
```bash
# Run all tests
cd hybrid-chatbot-project
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/test_integration.py
python -m pytest tests/test_security.py
python -m pytest tests/test_end_to_end.py

# Load testing
python -m pytest tests/test_load.py --users 100 --spawn-rate 10

# Run tests with coverage
cd backend
poetry run pytest --cov=api --cov=workers --cov=database --cov-report=html
```

## Installation Guide

### VDS Server Installation (Ubuntu 20.04+)

#### 1. System Dependencies
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
sudo apt install ca-certificates curl gnupg lsb-release -y
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER
```

#### 2. Backend Setup
```bash
cd hybrid-chatbot-project

# Install Python dependencies
pip install poetry
poetry install

# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source ~/.cargo/env

# Build Rust components
cd rust && cargo build --release && cd ..

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### Windows 11 RTX 4070 Installation

#### 1. System Requirements
- Windows 11 Pro 64-bit
- NVIDIA RTX 4070 with latest drivers (531.18 or later)
- CUDA Toolkit 12.x
- Python 3.10 or 3.11
- Visual Studio Build Tools

#### 2. Install Dependencies
```powershell
# Install Python 3.10/3.11 from python.org
# Install Git for Windows

# Install Python dependencies
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r llm_worker/requirements.txt

# Install Rust toolchain
winget install --id Rustlang.Rustup
refreshenv
rustup default stable
```

#### 3. Install NVIDIA Tools
```powershell
# Install CUDA Toolkit 12.x
# Install cuDNN (download from NVIDIA developer site)
# Install TensorRT (download from NVIDIA developer site)

# Install TensorRT-LLM
pip install tensorrt-llm --index-url https://pypi.nvidia.com
```

#### 4. Model Preparation
```powershell
# Create models directory
mkdir models
cd models

# Download Qwen3-8B model or convert your own
# For example, download from Hugging Face:
git clone https://huggingface.co/Qwen/Qwen3-8B-Instruct-GGUF

# Convert to TensorRT format
cd ../llm_worker
python -m src.python.tensorrt_converter --model_path ../models/Qwen3-8B-Instruct-GGUF --output_dir ../models/trt_models/Qwen3-8B-Q5_K_M.plan --precision float16 --quantization weight_only_int8
```

## Performance Optimizations

### RTX 4070 Specific Optimizations

#### 1. TensorRT Configuration
- Use FP16 precision for optimal performance/accuracy balance
- Apply INT8 quantization for memory efficiency
- Enable cuBLASLt for better GEMM performance
- Set appropriate max workspace size (2GB recommended)

#### 2. Memory Management
- Use 85% of available GPU memory for model operations
- Implement proper memory allocation tracking
- Enable automatic memory cleanup
- Monitor memory usage during inference

#### 3. Concurrency Settings
- Configure optimal batch size (4 recommended for RTX 4070)
- Set appropriate max concurrent requests (4+)
- Implement proper request queuing with priority support
- Monitor GPU utilization for optimal performance

### Example Configuration for RTX 4070
```python
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
```

This comprehensive architecture provides a robust, scalable, and high-performance solution for running LLMs on RTX 4070 GPUs while maintaining security and proper resource management.