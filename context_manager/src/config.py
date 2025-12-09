"""
Configuration for the Context Management System
"""

import os
from typing import Dict, Any


class ContextManagerConfig:
    """
    Configuration class for context management system
    """
    
    # Model configuration
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    
    # Vector database configuration
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./context_memory.lancedb")
    
    # Performance settings
    MAX_CONTEXT_SIZE: int = int(os.getenv("MAX_CONTEXT_SIZE", "2000"))  # Max characters in context
    COMPRESSION_RATIO: float = float(os.getenv("COMPRESSION_RATIO", "0.5"))  # Default compression ratio
    MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "10"))  # Max results from semantic search
    MIN_IMPORTANCE_SCORE: float = float(os.getenv("MIN_IMPORTANCE_SCORE", "0.3"))  # Min score for important memories
    
    # Memory settings
    MEMORY_RETENTION_DAYS: int = int(os.getenv("MEMORY_RETENTION_DAYS", "30"))  # How long to keep memories
    MAX_MEMORY_SIZE: int = int(os.getenv("MAX_MEMORY_SIZE", "10000"))  # Max number of memories per user
    
    # Clustering settings
    CLUSTERING_THRESHOLD: float = float(os.getenv("CLUSTERING_THRESHOLD", "0.7"))  # Similarity threshold for clustering
    MAX_CLUSTERS: int = int(os.getenv("MAX_CLUSTERS", "None") if os.getenv("MAX_CLUSTERS") != "None" else None)  # Max clusters (None for auto)
    
    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_WORKERS: int = int(os.getenv("API_WORKERS", "1"))
    
    # Security settings
    ENABLE_ENCRYPTION: bool = os.getenv("ENABLE_ENCRYPTION", "False").lower() == "true"
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # Cache settings
    CACHE_SIZE: int = int(os.getenv("CACHE_SIZE", "1000"))  # Number of items to cache
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # Time-to-live in seconds
    
    # Performance optimization
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))  # Batch size for processing
    EMBEDDING_CACHE_ENABLED: bool = os.getenv("EMBEDDING_CACHE_ENABLED", "True").lower() == "true"
    EMBEDDING_CACHE_DIR: str = os.getenv("EMBEDDING_CACHE_DIR", "./cache/embeddings")
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Return configuration as dictionary"""
        return {
            key: value for key, value in cls.__dict__.items() 
            if not key.startswith('_') and not callable(value) and not isinstance(value, classmethod)
        }
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate configuration values"""
        errors = []
        
        if cls.COMPRESSION_RATIO <= 0 or cls.COMPRESSION_RATIO > 1:
            errors.append("COMPRESSION_RATIO must be between 0 and 1")
        
        if cls.MIN_IMPORTANCE_SCORE < 0 or cls.MIN_IMPORTANCE_SCORE > 1:
            errors.append("MIN_IMPORTANCE_SCORE must be between 0 and 1")
        
        if cls.CLUSTERING_THRESHOLD < 0 or cls.CLUSTERING_THRESHOLD > 1:
            errors.append("CLUSTERING_THRESHOLD must be between 0 and 1")
        
        if cls.API_PORT < 1 or cls.API_PORT > 65535:
            errors.append("API_PORT must be between 1 and 65535")
        
        if errors:
            raise ValueError(f"Configuration validation errors: {'; '.join(errors)}")


# Initialize and validate config
try:
    ContextManagerConfig.validate_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    raise


# Example usage
if __name__ == "__main__":
    print("Context Manager Configuration:")
    for key, value in ContextManagerConfig.get_config().items():
        print(f"  {key}: {value}")