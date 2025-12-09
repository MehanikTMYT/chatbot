# Docker Deployment for Hybrid Chatbot System

This document describes how to build and deploy the hybrid chatbot system using Docker with support for multiple deployment environments (PC, VDS, etc.).

## Prerequisites

- Docker installed (version 20.10 or higher)
- Docker Compose installed (version 2.0 or higher)
- Git (to clone the repository if needed)

## Configuration

The system uses environment variables for configuration. Create a `.env` file based on the example:

```bash
cp .env.example .env
```

Then edit the `.env` file to match your deployment requirements:

- For **PC development**: Use default values
- For **VDS deployment**: Update `EXTERNAL_HOST` to your server IP/domain and adjust ports as needed

## Building the System

To build both frontend and backend Docker images, run:

```bash
./build-docker.sh
```

Or manually:

```bash
docker-compose build
```

## Running the System

### Development (PC)
Start the complete system with default configuration:

```bash
docker-compose up -d
```

### Production (VDS)
For VDS deployment with custom configuration:

```bash
# Set environment variables or ensure .env is properly configured
docker-compose up -d
```

### Alternative: Override specific variables
You can override specific variables without modifying the .env file:

```bash
BACKEND_EXTERNAL_PORT=8080 FRONTEND_EXTERNAL_PORT=80 docker-compose up -d
```

The system will start all services in detached mode:
- Frontend will be available at `http://<EXTERNAL_HOST>:<FRONTEND_EXTERNAL_PORT>` (default: `http://localhost`)
- Backend API will be available at `http://<EXTERNAL_HOST>:<BACKEND_EXTERNAL_PORT>` (default: `http://localhost:8000`)
- PostgreSQL database will be available at `http://<EXTERNAL_HOST>:<POSTGRES_PORT>` (default: `http://localhost:5432`)
- Redis cache will be available at `http://<EXTERNAL_HOST>:<REDIS_PORT>` (default: `http://localhost:6379`)

## Stopping the System

To stop all services:

```bash
docker-compose down
```

To stop and remove volumes (this will delete database data):

```bash
docker-compose down -v
```

## Service Configuration

The system consists of the following services:

### Backend
- Built from `Dockerfile.backend`
- Runs the Python FastAPI application
- Connects to PostgreSQL and Redis
- Exposes configurable port (default: 8000)
- Includes health checks for production readiness

### Frontend
- Built from `Dockerfile.frontend`
- Serves the React application through Nginx
- Exposes configurable port (default: 80)
- Automatically connects to backend service

### Database (PostgreSQL)
- Uses PostgreSQL 13 image
- Stores application data
- Data is persisted in a named volume
- Includes health checks for production readiness

### Cache (Redis)
- Uses Redis 6-alpine image
- Provides caching and session storage
- Includes persistence and health checks

## Environment Variables

The system uses the following key environment variables (defined in `.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `COMPOSE_PROJECT_NAME` | Docker Compose project name | hybrid-chatbot |
| `BACKEND_PORT` | Internal backend port | 8000 |
| `BACKEND_EXTERNAL_PORT` | External port for backend access | 8000 |
| `FRONTEND_PORT` | Internal frontend port | 80 |
| `FRONTEND_EXTERNAL_PORT` | External port for frontend access | 80 |
| `POSTGRES_DB` | PostgreSQL database name | chatbot |
| `POSTGRES_USER` | PostgreSQL username | chatbot_user |
| `POSTGRES_PASSWORD` | PostgreSQL password | secure_password_change_me |
| `POSTGRES_PORT` | External PostgreSQL port | 5432 |
| `REDIS_PORT` | External Redis port | 6379 |
| `EXTERNAL_HOST` | Host address for external access | localhost |

## Volumes

- `${POSTGRES_DATA_VOLUME}`: Persists PostgreSQL data between container restarts
- `${REDIS_DATA_VOLUME}`: Persists Redis data between container restarts
- `${APP_LOGS_VOLUME}`: Maps application logs to the host system

## Networks

- `${APP_NETWORK_NAME}`: Isolated network for internal service communication

## Multi-Device Deployment Scenarios

### Local Development (PC)
- Use default `.env` settings
- Access via `http://localhost`

### VDS/Server Deployment
- Update `EXTERNAL_HOST` to your server IP or domain
- Adjust ports if needed to avoid conflicts
- Configure firewall to allow traffic on exposed ports
- Consider using a reverse proxy (like Nginx) for SSL termination

### Container Orchestration (Docker Swarm/Kubernetes)
- The compose file follows best practices for orchestration
- May require additional configuration for load balancing and scaling

## Health Checks

All services include health checks to ensure proper startup and ongoing operation:
- Backend: Checks `/health` endpoint
- PostgreSQL: Uses `pg_isready` command
- Redis: Uses `redis-cli ping` command

## Troubleshooting

### If you encounter permission issues:
Make sure the `build-docker.sh` script is executable:
```bash
chmod +x build-docker.sh
```

### To view logs:
```bash
docker-compose logs -f
```

### To view specific service logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### To rebuild images:
```bash
docker-compose build --no-cache
```

### Check service health status:
```bash
docker-compose ps
```

## Production Considerations

For production deployments, ensure you:

- Update all security-related variables in `.env` (especially passwords and secret keys)
- Use a production-grade reverse proxy (Nginx, Traefik) with SSL certificates
- Configure firewall rules to restrict access appropriately
- Set up automated backups for the PostgreSQL database
- Monitor resource usage and scale accordingly
- Implement proper logging aggregation
- Use Docker secrets for sensitive information in container orchestrators
- Consider implementing CI/CD pipelines for automated deployments