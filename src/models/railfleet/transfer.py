"""
Transfer Service models for locomotive movements between locations.
"""
from sqlalchemy import Column, String, DateTime, Enum, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class TransferStatus(str, PyEnum):
    """Transfer plan status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransferPriority(str, PyEnum):
    """Transfer priority enumeration."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TransferPlan(Base):
    """Transfer Plan model for locomotive movements."""

    __tablename__ = "transfer_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id = Column(String(50), unique=True, nullable=False, index=True)

    # Origin and destination
    from_location = Column(String(255), nullable=False)
    to_location = Column(String(255), nullable=False)

    # Timing
    scheduled_departure_ts = Column(DateTime, nullable=False)
    scheduled_arrival_ts = Column(DateTime, nullable=False)
    actual_departure_ts = Column(DateTime, nullable=True)
    actual_arrival_ts = Column(DateTime, nullable=True)

    # Status and priority
    status = Column(Enum(TransferStatus), nullable=False, default=TransferStatus.DRAFT)
    priority = Column(Enum(TransferPriority), nullable=False, default=TransferPriority.NORMAL)

    # Planning metadata
    distance_km = Column(Integer, nullable=True)
    estimated_duration_min = Column(Integer, nullable=True)
    route_notes = Column(String(1000), nullable=True)

    # Additional data
    metadata_json = Column(JSON, nullable=True)  # Route details, restrictions, etc.

    # Timestamps (UTC)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<TransferPlan(plan_id='{self.plan_id}', {self.from_location}→{self.to_location}, status='{self.status}')>"


class TransferAssignment(Base):
    """Transfer Assignment model - assigns vehicles to transfer plans."""

    __tablename__ = "transfer_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_plan_id = Column(UUID(as_uuid=True), ForeignKey("transfer_plans.id", ondelete="CASCADE"), nullable=False)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)

    # Assignment details
    position_in_convoy = Column(Integer, nullable=True)  # For multi-vehicle transfers
    driver_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to staff

    # Status tracking
    is_confirmed = Column(String(50), nullable=False, default="pending")  # pending, confirmed, cancelled
    confirmation_notes = Column(String(500), nullable=True)

    # Timestamps (UTC)
    assigned_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    assigned_by = Column(UUID(as_uuid=True), nullable=True)

    def __repr__(self):
        return f"<TransferAssignment(plan_id={self.transfer_plan_id}, vehicle_id={self.vehicle_id}, status='{self.is_confirmed}')>"
