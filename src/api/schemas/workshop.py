"""
Workshop schemas.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class WorkshopCreate(BaseModel):
    """Create workshop."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    location: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    total_tracks: int = Field(1, ge=1)
    is_ecm_certified: bool = False
    specializations: Optional[List[str]] = None
    supported_vehicle_types: Optional[List[str]] = None


class WorkshopUpdate(BaseModel):
    """Update workshop."""
    name: Optional[str] = None
    location: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    total_tracks: Optional[int] = Field(None, ge=1)
    available_tracks: Optional[int] = Field(None, ge=0)
    is_ecm_certified: Optional[bool] = None
    specializations: Optional[List[str]] = None
    supported_vehicle_types: Optional[List[str]] = None
    is_active: Optional[bool] = None


class WorkshopResponse(BaseModel):
    """Workshop response."""
    id: str
    code: str
    name: str
    location: str
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    total_tracks: int
    available_tracks: int
    is_ecm_certified: bool
    specializations: Optional[List[str]] = None
    supported_vehicle_types: Optional[List[str]] = None
    rating: Optional[float] = None
    total_completed_orders: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
