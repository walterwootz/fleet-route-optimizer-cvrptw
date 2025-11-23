"""
Transfer service schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.models.railfleet.transfer import TransferStatus, TransferPriority


class TransferPlanBase(BaseModel):
    """Base transfer plan schema."""
    plan_id: str = Field(..., min_length=1, max_length=50)
    from_location: str = Field(..., min_length=1, max_length=255)
    to_location: str = Field(..., min_length=1, max_length=255)
    scheduled_departure_ts: datetime
    scheduled_arrival_ts: datetime
    priority: TransferPriority = TransferPriority.NORMAL
    distance_km: Optional[int] = Field(None, gt=0)
    estimated_duration_min: Optional[int] = Field(None, gt=0)
    route_notes: Optional[str] = Field(None, max_length=1000)
    metadata_json: Optional[Dict[str, Any]] = None


class TransferPlanCreate(TransferPlanBase):
    """Create transfer plan request."""
    status: TransferStatus = TransferStatus.DRAFT


class TransferPlanUpdate(BaseModel):
    """Update transfer plan request (partial updates allowed)."""
    from_location: Optional[str] = Field(None, min_length=1, max_length=255)
    to_location: Optional[str] = Field(None, min_length=1, max_length=255)
    scheduled_departure_ts: Optional[datetime] = None
    scheduled_arrival_ts: Optional[datetime] = None
    actual_departure_ts: Optional[datetime] = None
    actual_arrival_ts: Optional[datetime] = None
    status: Optional[TransferStatus] = None
    priority: Optional[TransferPriority] = None
    distance_km: Optional[int] = Field(None, gt=0)
    estimated_duration_min: Optional[int] = Field(None, gt=0)
    route_notes: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class TransferPlanResponse(TransferPlanBase):
    """Transfer plan response."""
    id: str
    status: TransferStatus
    actual_departure_ts: Optional[datetime] = None
    actual_arrival_ts: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class TransferPlanListResponse(BaseModel):
    """Transfer plans list response."""
    total: int
    plans: List[TransferPlanResponse]


class TransferAssignmentBase(BaseModel):
    """Base transfer assignment schema."""
    transfer_plan_id: str
    vehicle_id: str
    position_in_convoy: Optional[int] = Field(None, ge=1)
    driver_id: Optional[str] = None
    confirmation_notes: Optional[str] = Field(None, max_length=500)


class TransferAssignmentCreate(TransferAssignmentBase):
    """Create transfer assignment request."""
    pass


class TransferAssignmentUpdate(BaseModel):
    """Update transfer assignment request."""
    position_in_convoy: Optional[int] = Field(None, ge=1)
    driver_id: Optional[str] = None
    is_confirmed: Optional[str] = Field(None, pattern="^(pending|confirmed|cancelled)$")
    confirmation_notes: Optional[str] = None


class TransferAssignmentResponse(TransferAssignmentBase):
    """Transfer assignment response."""
    id: str
    is_confirmed: str
    assigned_at: datetime
    confirmed_at: Optional[datetime] = None
    assigned_by: Optional[str] = None

    class Config:
        from_attributes = True


class TransferAssignmentListResponse(BaseModel):
    """Transfer assignments list response."""
    total: int
    assignments: List[TransferAssignmentResponse]
