"""
HR Service models for staff and personnel assignment management.
"""
from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class StaffRole(str, PyEnum):
    """Staff role enumeration."""
    DRIVER = "driver"
    MECHANIC = "mechanic"
    TECHNICIAN = "technician"
    DISPATCHER = "dispatcher"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"


class StaffStatus(str, PyEnum):
    """Staff status enumeration."""
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SICK_LEAVE = "sick_leave"
    TRAINING = "training"
    INACTIVE = "inactive"


class Staff(Base):
    """Staff model for personnel management."""

    __tablename__ = "staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id = Column(String(50), unique=True, nullable=False, index=True)

    # Personal information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Employment details
    role = Column(Enum(StaffRole), nullable=False)
    status = Column(Enum(StaffStatus), nullable=False, default=StaffStatus.ACTIVE)
    employee_number = Column(String(50), nullable=True, index=True)

    # Skills and qualifications
    skills_json = Column(JSON, nullable=True)  # ["HU", "INSPECTION", "WELDING", etc.]
    certifications_json = Column(JSON, nullable=True)  # License numbers, validity dates

    # Work assignment details
    home_depot = Column(String(255), nullable=True)
    workshop_id = Column(UUID(as_uuid=True), ForeignKey("workshops.id"), nullable=True)
    max_weekly_hours = Column(Integer, default=40, nullable=False)

    # Availability
    is_available = Column(Boolean, default=True, nullable=False)
    availability_notes = Column(String(500), nullable=True)

    # Timestamps (UTC)
    hired_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Staff(staff_id='{self.staff_id}', name='{self.first_name} {self.last_name}', role='{self.role}')>"


class StaffAssignment(Base):
    """Staff Assignment model - assigns staff to work orders or shifts."""

    __tablename__ = "staff_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    staff_id = Column(UUID(as_uuid=True), ForeignKey("staff.id", ondelete="CASCADE"), nullable=False)

    # Assignment target (work order, shift, or transfer)
    work_order_id = Column(UUID(as_uuid=True), ForeignKey("work_orders.id", ondelete="CASCADE"), nullable=True)
    transfer_plan_id = Column(UUID(as_uuid=True), ForeignKey("transfer_plans.id", ondelete="CASCADE"), nullable=True)

    # Assignment timing
    scheduled_start_ts = Column(DateTime, nullable=False)
    scheduled_end_ts = Column(DateTime, nullable=False)
    actual_start_ts = Column(DateTime, nullable=True)
    actual_end_ts = Column(DateTime, nullable=True)

    # Assignment details
    role_on_assignment = Column(String(100), nullable=True)  # "Lead Mechanic", "Assistant", etc.
    status = Column(String(50), nullable=False, default="scheduled")  # scheduled, confirmed, in_progress, completed, cancelled

    # Hours tracking
    planned_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)

    # Notes
    assignment_notes = Column(String(500), nullable=True)

    # Timestamps (UTC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<StaffAssignment(staff_id={self.staff_id}, wo_id={self.work_order_id}, status='{self.status}')>"
