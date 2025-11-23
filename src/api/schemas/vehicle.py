"""
Vehicle schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from src.models.railfleet.vehicle import VehicleStatus, VehicleType


class VehicleBase(BaseModel):
    """Base vehicle schema."""
    asset_id: str = Field(..., min_length=1, max_length=50)
    model: str = Field(..., min_length=1, max_length=100)
    type: VehicleType
    manufacturer: Optional[str] = Field(None, max_length=100)
    year: Optional[int] = Field(None, ge=1900, le=2100)
    max_speed_kmh: Optional[int] = Field(None, gt=0)
    power_kw: Optional[int] = Field(None, gt=0)
    weight_tons: Optional[float] = Field(None, gt=0)
    current_location: Optional[str] = None
    home_depot: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)
    specifications: Optional[Dict[str, Any]] = None


class VehicleCreate(VehicleBase):
    """Create vehicle request."""
    status: VehicleStatus = VehicleStatus.AVAILABLE
    current_mileage_km: int = Field(0, ge=0)
    total_operating_hours: int = Field(0, ge=0)


class VehicleUpdate(BaseModel):
    """Update vehicle request (partial updates allowed)."""
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[VehicleStatus] = None
    manufacturer: Optional[str] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    current_mileage_km: Optional[int] = Field(None, ge=0)
    total_operating_hours: Optional[int] = Field(None, ge=0)
    current_location: Optional[str] = None
    home_depot: Optional[str] = None
    notes: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None


class VehicleResponse(VehicleBase):
    """Vehicle response."""
    id: str
    status: VehicleStatus
    current_mileage_km: int
    total_operating_hours: int
    created_at: datetime
    updated_at: datetime
    last_service_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class VehicleListResponse(BaseModel):
    """List of vehicles response."""
    total: int
    vehicles: list[VehicleResponse]
