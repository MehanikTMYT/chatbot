#!/bin/bash

echo "Building Docker images for the hybrid chatbot system..."

# Build both frontend and backend images
docker-compose build

echo "Docker images built successfully!"
echo "To run the system, execute: docker-compose up -d"
echo "To stop the system, execute: docker-compose down"