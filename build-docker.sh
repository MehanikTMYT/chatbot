#!/bin/bash

echo "Building Docker images for the hybrid chatbot system..."
echo "Usage: $0 [environment]"
echo "  environment: dev|prod|vds (default: dev)"
echo ""

ENVIRONMENT=${1:-dev}
ENV_FILE=".env"

# Check if .env file exists, if not use .env.example
if [ ! -f "$ENV_FILE" ]; then
    echo "Warning: $ENV_FILE not found, using .env.example as template"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "Created .env from .env.example - please review and customize before deployment"
        ENV_FILE=".env"
    else
        echo "No environment file found, proceeding with default environment variables"
        ENV_FILE=""
    fi
fi

# Set environment-specific variables
case $ENVIRONMENT in
    "prod"|"vds")
        echo "Building for production/VDS environment"
        # In production/VDS, we might want to pull latest images
        docker-compose pull --ignore-pull-failures
        ;;
    "dev")
        echo "Building for development environment"
        ;;
    *)
        echo "Unknown environment: $ENVIRONMENT, using development settings"
        ENVIRONMENT="dev"
        ;;
esac

# Build the images
if [ -n "$ENV_FILE" ] && [ -f "$ENV_FILE" ]; then
    # Use the environment file
    docker-compose --env-file "$ENV_FILE" build
else
    # Use default environment variables
    docker-compose build
fi

if [ $? -eq 0 ]; then
    echo ""
    echo "Docker images built successfully!"
    echo ""
    echo "To run the system in development mode:"
    echo "  docker-compose up -d"
    echo ""
    echo "To run the system in production/VDS mode:"
    echo "  docker-compose --env-file .env up -d"
    echo ""
    echo "To stop the system:"
    echo "  docker-compose down"
    echo ""
else
    echo "Build failed!"
    exit 1
fi