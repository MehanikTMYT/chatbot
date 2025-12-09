"""
Configuration module for the Hybrid Chatbot System
Handles environment variables and application settings
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_TITLE: str = os.getenv("API_TITLE", "Hybrid Chatbot API")
    API_VERSION: str = os.getenv("API_VERSION", "0.1.0")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://chatbot:password123@localhost:3306/chatbot_db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "20"))
    DATABASE_POOL_OVERFLOW: int = int(os.getenv("DATABASE_POOL_OVERFLOW", "10"))
    
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    REDIS_PREFIX: str = os.getenv("REDIS_PREFIX", "chatbot:")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # JWT Configuration
    JWT_ISSUER: str = os.getenv("JWT_ISSUER", "hybrid-chatbot")
    JWT_AUDIENCE: str = os.getenv("JWT_AUDIENCE", "hybrid-chatbot-users")
    
    # Vector Database
    LANCEDB_URI: str = os.getenv("LANCEDB_URI", "./vector_storage")
    
    # Workers Configuration
    WORKER_HOST: str = os.getenv("WORKER_HOST", "0.0.0.0")
    WORKER_PORT: int = int(os.getenv("WORKER_PORT", "8002"))
    WORKER_HEARTBEAT_INTERVAL: int = int(os.getenv("WORKER_HEARTBEAT_INTERVAL", "30"))
    WORKER_TIMEOUT: int = int(os.getenv("WORKER_TIMEOUT", "60"))
    
    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "32_character_base64_encoded_key_here")
    TUNNEL_TIMEOUT: int = int(os.getenv("TUNNEL_TIMEOUT", "300"))
    
    # Frontend
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOG_FILE: str = os.getenv("LOG_FILE", "./logs/app.log")
    ERROR_LOG_FILE: str = os.getenv("ERROR_LOG_FILE", "./logs/error.log")
    
    # Security
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", '["http://localhost:3000", "http://localhost:8000"]').replace("'", '"')
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", '["*"]').replace("'", '"')
    
    # ML Configuration
    TENSORRT_ENGINE_PATH: str = os.getenv("TENSORRT_ENGINE_PATH", "./engines/")
    MODEL_CACHE_DIR: str = os.getenv("MODEL_CACHE_DIR", "./models/")
    MAX_CONTEXT_LENGTH: int = int(os.getenv("MAX_CONTEXT_LENGTH", "4096"))
    MAX_GENERATION_LENGTH: int = int(os.getenv("MAX_GENERATION_LENGTH", "1024"))
    
    # Performance
    WORKERS_COUNT: int = int(os.getenv("WORKERS_COUNT", "4"))
    CONCURRENT_REQUESTS: int = int(os.getenv("CONCURRENT_REQUESTS", "100"))

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Initialize database engine
from sqlalchemy.ext.asyncio import create_async_engine
DB_ENGINE = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_POOL_OVERFLOW,
    echo=False  # Set to True for SQL debugging
)

# Process JSON-like environment variables
import json
try:
    settings.CORS_ORIGINS = json.loads(settings.CORS_ORIGINS)
except json.JSONDecodeError:
    settings.CORS_ORIGINS = ["*"]

try:
    settings.ALLOWED_HOSTS = json.loads(settings.ALLOWED_HOSTS)
except json.JSONDecodeError:
    settings.ALLOWED_HOSTS = ["*"]