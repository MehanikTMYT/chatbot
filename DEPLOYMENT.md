# Deployment Guide for Hybrid Chatbot System

This guide explains how to deploy the Hybrid Chatbot System in different configurations based on your needs.

## Configuration Options

The system supports multiple deployment configurations:

1. **All-in-One (Development)** - All services on a single machine for development
2. **VDS (Frontend Only)** - Frontend service only on a VDS, connecting to external backend
3. **Distributed** - Different services on different machines

## Prerequisites

- Docker Engine (v20.10.0 or later)
- Docker Compose (v2.0.0 or later)
- At least 4GB RAM for all-in-one deployment
- For LLM workers: NVIDIA GPU with CUDA support (optional)

## Environment Configuration

Create an `.env` file in the project root with the following variables:

```bash
# Database configuration
MYSQL_ROOT_PASSWORD=rootpassword123
MYSQL_DATABASE=chatbot_db
MYSQL_USER=chatbot
MYSQL_PASSWORD=password123
DATABASE_URL=mysql+pymysql://chatbot:password123@db:3306/chatbot_db

# Redis configuration
REDIS_URL=redis://redis:6379

# Security
SECRET_KEY=your-very-long-secret-key-change-in-production

# Service ports
BACKEND_EXTERNAL_PORT=8000
FRONTEND_EXTERNAL_PORT=3000
MYSQL_PORT=3306
REDIS_PORT=6379

# Backend configuration
BACKEND_ENV=production
BACKEND_PORT=8000

# Frontend configuration
FRONTEND_PORT=3000

# Volumes
MYSQL_DATA_VOLUME=mysql_data
REDIS_DATA_VOLUME=redis_data
APP_LOGS_VOLUME=app_logs

# Network
APP_NETWORK_NAME=app-network

# Worker selection (use with docker-compose.workers.yml)
# Enable specific workers by setting environment variables:
# COMPOSE_PROFILES=llm,web,vector,monitoring
```

## Deployment Scenarios

### 1. All-in-One Development Setup

Run all services on a single machine for development:

```bash
# Copy the example environment file
cp .env.example .env

# Start all services with development settings
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

This setup includes:
- Backend API service
- Frontend service
- MySQL database
- Redis cache

### 2. Production All-in-One Setup

Run all services on a single machine for production:

```bash
# Start all services with production settings
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. VDS (Frontend Only) Setup

Run only the frontend service on a VDS, connecting to an external backend:

```bash
# Set the external backend URL in your .env file:
# BACKEND_API_URL=https://your-backend-domain.com

# Start only the frontend service
docker-compose -f docker-compose.yml -f docker-compose.vds.yml up -d
```

### 4. Worker Services

To run computational workers (LLM, Web, Vector), use the workers configuration:

```bash
# Start all services plus workers
docker-compose -f docker-compose.yml -f docker-compose.local.yml -f docker-compose.workers.yml --profile llm --profile web up

# Or start specific worker profiles:
# --profile llm (for LLM inference workers)
# --profile web (for web search workers)
# --profile vector (for vector database workers)
# --profile monitoring (for monitoring services)
```

### 5. Selective Worker Deployment

You can select which workers to run using environment variables:

```bash
# Run only LLM workers
COMPOSE_PROFILES=llm docker-compose -f docker-compose.yml -f docker-compose.workers.yml up -d

# Run LLM and Web workers
COMPOSE_PROFILES=llm,web docker-compose -f docker-compose.yml -f docker-compose.workers.yml up -d

# Run all workers
COMPOSE_PROFILES=llm,web,vector,monitoring docker-compose -f docker-compose.yml -f docker-compose.workers.yml up -d
```

## Service URLs

After deployment, access the services at:

- **Frontend**: http://localhost:3000 (or http://your-vds-ip:3000)
- **Backend API**: http://localhost:8000 (or http://your-backend-ip:8000)
- **MySQL**: localhost:3306 (internal only)
- **Redis**: localhost:6379 (internal only)

## Scaling Services

To scale specific services:

```bash
# Scale backend service to 2 instances
docker-compose -f docker-compose.yml up -d --scale backend=2

# Scale frontend service
docker-compose -f docker-compose.yml up -d --scale frontend=2
```

## Monitoring and Logs

Check service status and logs:

```bash
# View all service logs
docker-compose -f docker-compose.yml logs

# View specific service logs
docker-compose -f docker-compose.yml logs backend
docker-compose -f docker-compose.yml logs frontend

# Monitor service health
docker-compose -f docker-compose.yml ps
```

## Stopping Services

To stop all services:

```bash
# Stop all services
docker-compose -f docker-compose.yml down

# Stop with volumes removal (data will be lost)
docker-compose -f docker-compose.yml down -v
```

## Troubleshooting

### Database Connection Issues
- Ensure the database service is running: `docker-compose ps`
- Check database logs: `docker-compose logs db`
- Verify DATABASE_URL in your .env file

### Frontend Cannot Connect to Backend
- Check that the BACKEND_URL environment variable is set correctly
- Verify the backend service is accessible from the frontend container
- Check CORS settings in the backend configuration

### Worker Services Not Starting
- Verify that the database and Redis services are running before starting workers
- Check that the required environment variables are set
- Ensure the worker profiles are enabled when starting the services