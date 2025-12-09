# Hybrid Chatbot System

A distributed hybrid chatbot system with computational workers running on local Windows 11 machines with NVIDIA RTX GPUs and frontend/API gateway/database hosted on a VDS server.

## Architecture Overview

### Components
- **VDS Server**: API Gateway (FastAPI), Frontend (Vue 3), Database (MySQL), Cache (Redis)
- **Local Workers**: LLM processing on Windows 11 with RTX 4070 GPUs using TensorRT optimization
- **Security**: End-to-end encryption using Rust cryptography, secure tunneling between VDS and workers

### Technology Stack
- **Languages**: Python, TypeScript, JavaScript, Rust
- **Frontend**: Vue 3 + Vite + TypeScript + Pinia
- **Backend**: FastAPI, SQLAlchemy, Redis, LanceDB
- **ML Infrastructure**: TensorRT-LLM, Sentence Transformers, PyTorch
- **System Components**: WebSockets, Rust-native modules for performance

### Key Features
- Distributed architecture with clear separation between VDS and local workers
- Privacy-focused design with no subscriptions required
- High-performance inference using TensorRT optimization
- Secure communication with Rust-based encryption
- Real-time WebSocket connections
- Vector memory with semantic search capabilities

## Prerequisites

### VDS Server Requirements
- Linux distribution (Ubuntu 20.04+ recommended)
- Docker and Docker Compose
- 4GB+ RAM, 2+ CPU cores
- Public IP address for API access

### Local Worker Requirements (Windows 11)
- Windows 11 Pro (64-bit)
- NVIDIA RTX 4070 or equivalent GPU
- CUDA-compatible drivers installed
- Python 3.10+
- Rust toolchain

## Setup Instructions

### Initial Setup
```bash
# Clone the repository
git clone <repository-url>
cd hybrid-chatbot

# Initialize submodules (if any)
git submodule update --init --recursive
```

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

#### 3. Database Setup
```bash
# Using Docker Compose (recommended for VDS)
docker-compose up -d db redis

# Or set up MySQL manually
# Create database and user for the application
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

#### 5. Run LLM Worker
```powershell
cd llm_worker
python main.py --model-path ../models/trt_models/Qwen3-8B-Q5_K_M.plan --tokenizer-path ../models/Qwen3-8B-Instruct-GGUF --api-host 0.0.0.0 --api-port 8000
```

### Development Environment Setup

#### Backend (VDS)
```bash
cd hybrid-chatbot-project/backend
pip install poetry
poetry install
```

#### Frontend
```bash
cd hybrid-chatbot-project/frontend
npm install
```

#### Workers
```bash
cd hybrid-chatbot-project
pip install -r llm_worker/requirements.txt
```

#### Rust Components
```bash
cd hybrid-chatbot-project/rust
cargo build --release
```

### Configuration
Copy `.env.example` to `.env` and configure the appropriate settings for your environment:

```bash
# Database settings
DB_HOST=localhost
DB_PORT=3306
DB_USER=chatbot_user
DB_PASSWORD=secure_password
DB_NAME=hybrid_chatbot

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379

# API settings
API_HOST=0.0.0.0
API_PORT=8000

# Security settings
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Worker settings
WORKER_API_URL=http://localhost:8000
WORKER_AUTH_TOKEN=your_worker_auth_token
```

### Running the Application

#### VDS Server (Production)
```bash
# Start all services with Docker Compose
docker-compose up -d --build

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

#### Windows 11 Worker (Local)
```bash
# Start LLM worker
cd llm_worker
python main.py

# Start web worker (if needed)
cd web_worker
python main.py
```

#### Development Mode
```bash
# Backend API
cd hybrid-chatbot-project/backend
poetry run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd hybrid-chatbot-project/frontend
npm run dev

# Or run individual components separately
# Frontend: cd frontend && npm run dev
# Backend: cd backend && poetry run uvicorn api.main:app --reload
```

## Testing Strategy

### White Box Testing
White box testing focuses on internal structures and implementation details:

#### 1. Unit Tests
- Test individual functions and methods
- Test edge cases and error conditions
- Test data validation and sanitization

#### 2. Integration Tests
- Test component interactions
- Test API endpoints with various inputs
- Test database operations
- Test worker communication

#### 3. Code Coverage
```bash
# Run tests with coverage
cd backend
poetry run pytest --cov=api --cov=workers --cov=database --cov-report=html

# Check coverage report
open htmlcov/index.html
```

#### 4. Memory Leak Detection
- Monitor memory usage during long-running operations
- Test garbage collection effectiveness
- Validate resource cleanup

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
```

## Project Structure
```
hybrid-chatbot/
├── backend/        # Python backend components
│   ├── api/        # FastAPI gateway
│   ├── core/       # Common logic, utilities
│   ├── database/   # Models and SQLAlchemy sessions
│   ├── workers/    # Base worker classes
│   └── config/     # Configuration
├── frontend/       # Vue 3 + Vite + TypeScript
│   ├── src/
│   │   ├── components/    # Reusable components
│   │   ├── views/         # Application pages
│   │   ├── stores/        # Pinia stores
│   │   ├── composables/   # Vue composables
│   │   ├── types/         # TypeScript types
│   │   ├── utils/         # Utilities
│   │   ├── assets/        # Static files
│   │   ├── router/        # Vue Router
│   │   └── App.vue        # Root component
│   ├── vite.config.ts     # Vite configuration
│   ├── tsconfig.json      # TypeScript config
│   └── index.html         # Entry point
├── workers/        # Local workers
│   ├── llm-worker/        # Python + Rust for LLM
│   ├── web-worker/        # Python for web-search
│   └── native/            # Rust modules for native acceleration
├── scripts/        # Helper scripts in Python/JS
├── deployment/     # Docker, Kubernetes, nginx configs
├── docs/           # Documentation
├── .github/        # CI/CD workflows
├── rust/           # Common Rust components
│   ├── crypto/     # Cryptography for tunnels
│   ├── tensorrt/   # Native bindings for TensorRT
│   └── utils/      # Common utilities
├── pyproject.toml  # Python dependencies and metadata
├── Cargo.toml      # Rust dependencies and metadata
├── package.json    # Frontend dependencies
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

## Security Considerations
- All sensitive data stored in .env files
- End-to-end encryption for communication
- Input validation at all levels
- XSS protection through Vue auto-escaping
- Regular dependency vulnerability audits

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License
[License information to be added]