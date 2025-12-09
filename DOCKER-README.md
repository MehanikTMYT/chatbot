# Docker Deployment for Hybrid Chatbot System

This document describes how to build and deploy the hybrid chatbot system using Docker.

## Prerequisites

- Docker installed (version 20.10 or higher)
- Docker Compose installed (version 2.0 or higher)

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

To start the complete system with all services:

```bash
docker-compose up -d
```

The system will start all services in detached mode:
- Frontend will be available at `http://localhost`
- Backend API will be available at `http://localhost:8000`
- PostgreSQL database will be available at `http://localhost:5432`
- Redis cache will be available at `http://localhost:6379`

## Stopping the System

To stop all services:

```bash
docker-compose down
```

## Service Configuration

The system consists of the following services:

### Backend
- Built from `Dockerfile.backend`
- Runs the Python FastAPI application
- Connects to PostgreSQL and Redis
- Exposes port 8000

### Frontend
- Built from `Dockerfile.frontend`
- Serves the React application through Nginx
- Exposes port 80

### Database (PostgreSQL)
- Uses PostgreSQL 13 image
- Stores application data
- Data is persisted in a named volume

### Cache (Redis)
- Uses Redis 6-alpine image
- Provides caching and session storage

## Environment Variables

The system uses the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

These are configured in the `docker-compose.yml` file.

## Volumes

- `postgres_data`: Persists PostgreSQL data between container restarts
- `./logs`: Maps application logs to the host system

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

### To rebuild images:
```bash
docker-compose build --no-cache
```

## Production Considerations

For production deployments, consider:
- Using production-grade secrets management
- Configuring SSL certificates
- Setting up proper monitoring
- Implementing backup strategies for the database
- Adding a reverse proxy like Traefik or Nginx for load balancing