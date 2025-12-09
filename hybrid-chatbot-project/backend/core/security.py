"""
Security module for the Hybrid Chatbot System
Handles authentication, authorization, and encryption
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer
import os

from core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a hash for the given password"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(security)) -> dict:
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(
            token.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            audience=[settings.JWT_AUDIENCE],
            issuer=settings.JWT_ISSUER
        )
        
        # Check if token is expired
        if datetime.fromtimestamp(payload.get("exp", 0)) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return payload
    except jwt.exceptions.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_access_token(token: str = Depends(security)) -> dict:
    """Verify JWT access token specifically"""
    payload = verify_token_raw(token)
    token_type = payload.get("type")
    
    if token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

def verify_token_raw(token: str = Depends(security)) -> dict:
    """Raw token verification without type checking"""
    try:
        payload = jwt.decode(
            token.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=[settings.JWT_AUDIENCE],
            issuer=settings.JWT_ISSUER
        )
        return payload
    except jwt.exceptions.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Import Rust crypto module if available
try:
    from rust.crypto import PyCryptoService
    rust_crypto_available = True
    
    # Initialize crypto service with encryption key
    crypto_service = PyCryptoService(key=settings.ENCRYPTION_KEY.encode())
except ImportError:
    rust_crypto_available = False
    crypto_service = None

def encrypt_data(data: str) -> str:
    """Encrypt data using Rust crypto module if available, otherwise use basic method"""
    if rust_crypto_available and crypto_service:
        encrypted_bytes = crypto_service.encrypt(data.encode())
        return bytes(encrypted_bytes).hex()
    else:
        # Fallback encryption (not secure, for development only)
        import base64
        encoded = base64.b64encode(data.encode()).decode()
        return encoded

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using Rust crypto module if available, otherwise use basic method"""
    if rust_crypto_available and crypto_service:
        encrypted_bytes = bytes.fromhex(encrypted_data)
        decrypted_bytes = crypto_service.decrypt(list(encrypted_bytes))
        return bytes(decrypted_bytes).decode()
    else:
        # Fallback decryption (not secure, for development only)
        import base64
        decoded = base64.b64decode(encrypted_data.encode()).decode()
        return decoded