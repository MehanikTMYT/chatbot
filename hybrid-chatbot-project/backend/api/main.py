"""
Main API Gateway for the Hybrid Chatbot System
This serves as the entry point for the FastAPI application
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import logging
import os
from typing import AsyncGenerator, Optional

from core.config import settings
from core.security import verify_token
from database.session import get_db, init_db
from api.routers import auth, chat, workers, characters
from api.routers.monitoring import router as monitoring_router
from workers.worker_manager import worker_manager

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized successfully")
    
    # Initialize worker manager
    logger.info("Initializing worker manager...")
    await worker_manager.initialize()
    await worker_manager.start_monitoring()
    logger.info("Worker manager initialized successfully")
    
    yield  # Application runs here
    
    logger.info("Shutting down worker manager...")
    await worker_manager.stop_monitoring()
    
    logger.info("Shutting down application...")

# Create FastAPI app with lifespan
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="A distributed hybrid chatbot system with computational workers running on local Windows 11 machines with NVIDIA RTX GPUs",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Expose headers for authentication
    expose_headers=["Access-Control-Allow-Origin"]
)

# Add security scheme
security = HTTPBearer()

# Include API routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(workers.router, prefix="/api/v1/workers", tags=["Workers"])
app.include_router(characters.router, prefix="/api/v1/characters", tags=["Characters"])
app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["Monitoring"])

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "message": "Hybrid Chatbot API Gateway",
        "version": settings.API_VERSION,
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.API_VERSION,
        "timestamp": __import__('time').time()
    }

@app.get("/api/v1/config")
async def get_client_config(current_user: dict = Depends(verify_token)):
    """Get client configuration for frontend"""
    return {
        "websocket_url": f"ws://{settings.API_HOST}:{settings.API_PORT}/ws",
        "api_version": settings.API_VERSION,
        "features": {
            "realtime_chat": True,
            "character_system": True,
            "secure_tunneling": True,
            "vector_search": True
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )