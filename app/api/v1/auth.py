"""
Authentication API endpoints for user registration and login.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import base64
import json
import hashlib
from typing import Optional

# Create router
router = APIRouter()

# Secret key for token generation
# In production, this should be set as an environment variable
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-for-development")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Mock user database for development
# In production, this would be replaced with a real database
USERS_DB = {
    "user@example.com": {
        "name": "Example User",
        "email": "user@example.com",
        "password": "password123",  # In production, this would be hashed
    }
}


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a simple encoded token (not JWT)."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire.timestamp()})
    
    # Convert to JSON and encode in base64
    json_str = json.dumps(to_encode)
    token = base64.b64encode(json_str.encode()).decode()
    
    # Add a simple signature
    signature = hashlib.sha256((token + SECRET_KEY).encode()).hexdigest()
    
    return f"{token}.{signature}"


@router.post("/auth/register")
async def register(user: UserCreate):
    """Register a new user."""
    if user.email in USERS_DB:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # In production, password would be hashed
    USERS_DB[user.email] = {
        "name": user.name,
        "email": user.email,
        "password": user.password,  # Would be hashed in production
    }
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": user.email, "name": user.name}
    )
    
    return {
        "status": "success",
        "message": "User registered successfully",
        "payload": {
            "token": access_token,
            "user": {
                "name": user.name,
                "email": user.email
            }
        }
    }


@router.post("/auth/login")
async def login(user: UserLogin):
    """Authenticate a user and return a token."""
    if user.email not in USERS_DB:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    stored_user = USERS_DB[user.email]
    if stored_user["password"] != user.password:  # In production, would compare hashed passwords
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    
    # Generate access token
    access_token = create_access_token(
        data={"sub": user.email, "name": stored_user["name"]}
    )
    
    return {
        "status": "success",
        "message": "Login successful",
        "payload": {
            "token": access_token,
            "user": {
                "name": stored_user["name"],
                "email": user.email
            }
        }
    }
