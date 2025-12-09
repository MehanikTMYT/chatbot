"""
Database models for the Hybrid Chatbot System
Defines SQLAlchemy models for all entities
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    """User model for authentication and authorization"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    characters = relationship("Character", back_populates="owner")

class Conversation(Base):
    """Conversation model for chat history"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    character = relationship("Character")
    messages = relationship("Message", back_populates="conversation", order_by="Message.timestamp")

class Message(Base):
    """Message model for individual chat messages"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # 'user' or 'bot'
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=func.now())
    metadata = Column(JSON)  # Additional message metadata
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

class Character(Base):
    """Character model for AI personalities"""
    __tablename__ = "characters"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    system_prompt = Column(Text)  # The core personality/prompt
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who created it
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Who owns it
    is_public = Column(Boolean, default=False)  # Whether other users can access
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    metadata = Column(JSON)  # Additional character metadata
    
    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="characters")
    creator = relationship("User", foreign_keys=[creator_id])

class Worker(Base):
    """Worker model for tracking computational workers"""
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(String(100), unique=True, nullable=False)  # Unique ID for the worker
    name = Column(String(100), nullable=False)
    host = Column(String(100), nullable=False)
    port = Column(Integer, nullable=False)
    gpu_model = Column(String(100))  # e.g., "NVIDIA RTX 4070"
    gpu_memory = Column(Integer)  # in MB
    total_memory = Column(Integer)  # in MB
    cpu_count = Column(Integer)
    status = Column(String(20), default="offline")  # 'online', 'offline', 'busy'
    last_heartbeat = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    capabilities = Column(JSON)  # What the worker can do (LLM, web search, etc.)
    performance_metrics = Column(JSON)  # Performance statistics
    
    # Relationships
    tasks = relationship("Task", back_populates="worker")

class Task(Base):
    """Task model for tracking distributed tasks"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False)  # UUID
    task_type = Column(String(50), nullable=False)  # 'llm_inference', 'web_search', etc.
    status = Column(String(20), default="pending")  # 'pending', 'processing', 'completed', 'failed'
    priority = Column(Integer, default=0)  # Higher number = higher priority
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)
    assigned_worker_id = Column(Integer, ForeignKey("workers.id"), nullable=True)
    input_data = Column(JSON)
    result_data = Column(JSON)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    worker = relationship("Worker", back_populates="tasks")

class VectorStorage(Base):
    """Model for vector storage metadata (LanceDB integration)"""
    __tablename__ = "vector_storage"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # Name of the vector table
    description = Column(Text)
    dimension = Column(Integer, nullable=False)  # Vector dimension
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    metadata = Column(JSON)  # Additional vector storage metadata

class SystemConfig(Base):
    """Model for system configuration settings"""
    __tablename__ = "system_config"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    description = Column(Text)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())