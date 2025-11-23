"""
Maintenance and work order schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from src.models.railfleet.maintenance import (
    MaintenanceType,
    WorkOrderStatus,
    WorkOrderPriority,
)


class MaintenanceTaskCreate(BaseModel):
    """Create maintenance task."""
    vehicle_id: str
    type: MaintenanceType
    description: Optional[str] = None
    due_date: datetime
    due_mileage_km: Optional[int] = None


class MaintenanceTaskResponse(BaseModel):
    """Maintenance task response."""
    id: str
    vehicle_id: str
    type: MaintenanceType
    description: Optional[str] = None
    due_date: datetime
    due_mileage_km: Optional[int] = None
    is_overdue: bool
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class WorkOrderCreate(BaseModel):
    """Create work order."""
    vehicle_id: str
    workshop_id: Optional[str] = None
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    work_description: Optional[str] = None
    tasks: Optional[List[str]] = None  # List of task types


class WorkOrderUpdate(BaseModel):
    """Update work order."""
    status: Optional[WorkOrderStatus] = None
    priority: Optional[WorkOrderPriority] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    assigned_track: Optional[str] = None
    assigned_team: Optional[str] = None
    work_performed: Optional[str] = None
    findings: Optional[str] = None
    actual_cost: Optional[float] = None


class WorkOrderResponse(BaseModel):
    """Work order response."""
    id: str
    order_number: str
    vehicle_id: str
    workshop_id: Optional[str] = None
    status: WorkOrderStatus
    priority: WorkOrderPriority
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    work_description: Optional[str] = None
    work_performed: Optional[str] = None
    findings: Optional[str] = None
    tasks: Optional[List[str]] = None
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
