# AI Character Communication Platform

A secure platform for communicating with AI characters, designed for high availability and security.

## Architecture

- **VDS Server (12GB RAM)**: Nginx, FastAPI, MySQL, Redis, SMTP server
- **Local PC**: AI models (Qwen3-8B-GGUF), WebSocket server
- **Primary Channel**: WebSocket over TLS (port 8443)
- **Backup Channel**: Reverse SSH Tunnel

## Components

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, aioredis
- **Frontend**: Vue.js 3, TypeScript, Tailwind CSS (coming soon)
- **AI Models**: Qwen3-8B-GGUF (4-bit quantized for local PC)
- **Database**: MySQL 8.0 with InnoDB
- **Monitoring**: Prometheus + Grafana (coming soon)

## Getting Started

See the backend README for setup instructions.