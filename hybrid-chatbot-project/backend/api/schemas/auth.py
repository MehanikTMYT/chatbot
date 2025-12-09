"""
Authentication schemas for the Hybrid Chatbot System
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for user creation requests"""
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    password: str

class UserUpdate(BaseModel):
    """Schema for user update requests"""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    username: str
    email: EmailStr
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int  # in seconds

class TokenData(BaseModel):
    """Schema for token data"""
    username: Optional[str] = None
    user_id: Optional[int] = None

class LoginRequest(BaseModel):
    """Schema for login requests"""
    username: str
    password: str