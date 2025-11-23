"""
HR service schemas for request/response validation.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.models.railfleet.hr import StaffRole, StaffStatus


class StaffBase(BaseModel):
    """Base staff schema."""
    staff_id: str = Field(..., min_length=1, max_length=50)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: StaffRole
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    employee_number: Optional[str] = Field(None, max_length=50)
    skills_json: Optional[List[str]] = None
    certifications_json: Optional[Dict[str, Any]] = None
    home_depot: Optional[str] = Field(None, max_length=255)
    workshop_id: Optional[str] = None
    max_weekly_hours: int = Field(40, ge=1, le=168)
    availability_notes: Optional[str] = Field(None, max_length=500)


class StaffCreate(StaffBase):
    """Create staff request."""
    status: StaffStatus = StaffStatus.ACTIVE
    is_available: bool = True
    hired_date: Optional[datetime] = None


class StaffUpdate(BaseModel):
    """Update staff request (partial updates allowed)."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    role: Optional[StaffRole] = None
    status: Optional[StaffStatus] = None
    skills_json: Optional[List[str]] = None
    certifications_json: Optional[Dict[str, Any]] = None
    home_depot: Optional[str] = None
    workshop_id: Optional[str] = None
    max_weekly_hours: Optional[int] = Field(None, ge=1, le=168)
    is_available: Optional[bool] = None
    availability_notes: Optional[str] = None


class StaffResponse(StaffBase):
    """Staff response."""
    id: str
    status: StaffStatus
    is_available: bool
    hired_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StaffListResponse(BaseModel):
    """Staff list response."""
    total: int
    staff: List[StaffResponse]


class StaffAssignmentBase(BaseModel):
    """Base staff assignment schema."""
    staff_id: str
    scheduled_start_ts: datetime
    scheduled_end_ts: datetime
    work_order_id: Optional[str] = None
    transfer_plan_id: Optional[str] = None
    role_on_assignment: Optional[str] = Field(None, max_length=100)
    planned_hours: Optional[int] = Field(None, ge=0)
    assignment_notes: Optional[str] = Field(None, max_length=500)


class StaffAssignmentCreate(StaffAssignmentBase):
    """Create staff assignment request."""
    status: str = Field("scheduled", pattern="^(scheduled|confirmed|in_progress|completed|cancelled)$")


class StaffAssignmentUpdate(BaseModel):
    """Update staff assignment request."""
    scheduled_start_ts: Optional[datetime] = None
    scheduled_end_ts: Optional[datetime] = None
    actual_start_ts: Optional[datetime] = None
    actual_end_ts: Optional[datetime] = None
    role_on_assignment: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(scheduled|confirmed|in_progress|completed|cancelled)$")
    planned_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    assignment_notes: Optional[str] = None


class StaffAssignmentResponse(StaffAssignmentBase):
    """Staff assignment response."""
    id: str
    status: str
    actual_start_ts: Optional[datetime] = None
    actual_end_ts: Optional[datetime] = None
    actual_hours: Optional[int] = None
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class StaffAssignmentListResponse(BaseModel):
    """Staff assignments list response."""
    total: int
    assignments: List[StaffAssignmentResponse]
