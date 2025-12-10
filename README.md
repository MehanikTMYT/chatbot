# Hybrid Chat-Bot with Adaptive Network and Rust Optimization

## 🎯 Overview
This is a local pet-project for a single user featuring a hybrid chat-bot with adaptive networking and Rust-optimized inference. The system operates in complete privacy without external subscriptions or cloud dependencies.

## 📋 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        VDS COMPONENT (STABLE)                   │
│                    chat.mehhost.ru (12GB RAM)                   │
├─────────────────────────────────────────────────────────────────┤
│ • Nginx Reverse Proxy                                           │
│ • API Gateway (FastAPI)                                         │
│ • Connection Manager (WebSocket/Long Polling)                 │
│ • JWT Authentication Service                                    │
│ • MySQL Database                                                │
│ • Network Configuration (Auto-detection)                       │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    │ (Adaptive Connection)
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LOCAL PC COMPONENT (DYNAMIC)                │
│              Windows 11 Pro, RTX 4070, i7 14-gen, 32GB RAM      │
├─────────────────────────────────────────────────────────────────┤
│ • Local Inference Server (FastAPI)                              │
│ • Rust-Optimized TensorRT Engine                                │
│ • Model Loader (with Python fallback)                           │
│ • Hardware Auto-Configuration                                   │
│ • Health Monitoring & Recovery                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🌐 Network Architecture

The system supports 4 modes of operation:
1. **Direct (LAN)** - Direct communication when both components on same network
2. **Relay (through VDS)** - Communication via VDS when direct connection unavailable
3. **Offline** - Local operation when no network connection available
4. **Hybrid** - Mixed mode with intelligent routing

## ⚡ Key Features

### Network Adaptation
- Automatic local IP detection for VDS ↔ PC communication
- Fallback from WebSocket to Long Polling when needed
- Runtime network parameter detection (no hardcoded IPs)

### Rust Optimization
- PyO3-based Rust library for inference acceleration
- Targeting 30%+ performance improvement on RTX 4070
- Automatic CUDA architecture detection (sm_89 for RTX 4070)
- Graceful fallback to Python on Rust errors

### Adaptive Frontend
- Vue3-based mobile-first design
- Cross-device session synchronization
- Offline message caching
- Real-time network status indicators

### Security
- JWT authentication with 24h timeout
- Automatic secret key generation on first run
- Offline token verification
- Local API protection from external calls

## 📁 Project Structure

```
chatbot-project/
├── .gitignore
├── .env.universal
├── README.md
├── requirements.txt          # VDS dependencies
├── requirements-local.txt    # Local PC dependencies
├── Cargo.toml                # Rust dependencies
├── docker-compose.yml        # Optional for local testing
├── nginx/
│   └── chatbot.conf
├── scripts/
│   ├── deploy_vds.sh
│   ├── setup_local.ps1       # Windows
│   └── setup_local.sh        # Linux/Mac
├── backend/
│   ├── main.py
│   ├── config/
│   │   ├── base_config.py
│   │   └── network_config.py
│   ├── services/
│   │   ├── api_gateway.py
│   │   ├── connection_manager.py
│   │   └── auth_service.py
│   ├── auth/
│   │   ├── jwt_manager.py
│   │   └── offline_verifier.py
│   └── first_run_setup.py
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── main.js
│       ├── router.js
│       ├── plugins/
│       │   ├── network.js
│       │   └── auth.js
│       ├── store/
│       │   ├── index.js
│       │   ├── auth.js
│       │   ├── chat.js
│       │   └── offline.js
│       ├── services/
│       │   ├── api.js
│       │   └── authService.js
│       ├── components/
│       │   ├── ChatInterface.vue
│       │   ├── MessageBubble.vue
│       │   ├── SessionList.vue
│       │   ├── LoginModal.vue
│       │   └── NetworkStatus.vue
│       ├── views/
│       │   ├── ChatView.vue
│       │   └── Dashboard.vue
│       └── App.vue
└── local-inference/          # ONLY FOR LOCAL PC
    ├── auto_config.py
    ├── connection.py
    ├── llm_server.py
    ├── health_check.py
    ├── fallback_engine.py
    ├── model_loader.py
    └── rust-core/            # Rust optimization
        ├── Cargo.toml
        └── src/
            ├── lib.rs
            ├── tensorrt.rs
            ├── preprocessing.rs
            └── network.rs
```

## 🚀 Setup Instructions

### VDS Setup (One-time, stable configuration)
1. Deploy the backend components on your VDS
2. Configure nginx with the provided configuration
3. Set up the database and initial configuration
4. The VDS structure remains unchanged after first deployment

### Local PC Setup
1. Run the setup script for your OS
2. The system will auto-detect your hardware (RTX 4070)
3. Rust optimization will be compiled for your specific GPU
4. Connection parameters will be auto-configured

## ✅ MVP Criteria
- [ ] Registration/login with JWT
- [ ] Auto network detection on first run
- [ ] Adaptive chat interface with responsive design
- [ ] Rust module compiles for RTX 4070
- [ ] Works in offline mode when connection is lost