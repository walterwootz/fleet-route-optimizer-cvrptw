"""
Authentication and authorization schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from src.core.security import Role


# Request Schemas
class UserRegister(BaseModel):
    """User registration request."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: Role = Role.VIEWER


class UserLogin(BaseModel):
    """User login request."""
    username: str
    password: str


class TokenRefresh(BaseModel):
    """Token refresh request."""
    refresh_token: str


# Response Schemas
class Token(BaseModel):
    """Token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response (no sensitive data)."""
    id: str
    username: str
    email: str
    role: Role
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Token payload data."""
    sub: str  # subject (user_id)
    role: Role
    exp: datetime
