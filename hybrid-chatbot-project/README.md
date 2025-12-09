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

### Development Environment Setup

#### Backend (VDS)
```bash
cd backend
pip install poetry
poetry install
```

#### Frontend
```bash
cd frontend
npm install
```

#### Workers
```bash
cd workers
pip install poetry
poetry install
```

#### Rust Components
```bash
cd rust
cargo build
```

### Configuration
Copy `.env.example` to `.env` and configure the appropriate settings for your environment.

### Running the Application

#### Development Mode
```bash
# Start all services with Docker Compose
docker-compose up --build

# Or run individual components separately
# Frontend: cd frontend && npm run dev
# Backend: cd backend && poetry run uvicorn api.main:app --reload
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