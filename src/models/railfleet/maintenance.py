"""
Maintenance models for tracking tasks and work orders.
"""
from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, Boolean, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class MaintenanceType(str, PyEnum):
    """Maintenance task types."""
    HU = "HU"  # Hauptuntersuchung (Main Inspection)
    INSPECTION = "INSPECTION"  # Regular inspection
    ECM = "ECM"  # ECM Certificate renewal
    REPAIR = "REPAIR"  # Unplanned repair
    PREVENTIVE = "PREVENTIVE"  # Preventive maintenance


class WorkOrderStatus(str, PyEnum):
    """Work order status."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderPriority(str, PyEnum):
    """Work order priority."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class MaintenanceTask(Base):
    """Maintenance task/requirement tracking."""

    __tablename__ = "maintenance_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    type = Column(Enum(MaintenanceType), nullable=False)
    description = Column(String(500), nullable=True)

    # Scheduling
    due_date = Column(DateTime, nullable=False)
    due_mileage_km = Column(Integer, nullable=True)
    is_overdue = Column(Boolean, default=False, nullable=False)

    # Status
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<MaintenanceTask(type='{self.type}', due_date='{self.due_date}')>"


class WorkOrder(Base):
    """Workshop work order."""

    __tablename__ = "work_orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_number = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "WO-2025-0012"

    # References
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    workshop_id = Column(UUID(as_uuid=True), ForeignKey("workshops.id"), nullable=True)

    # Status and priority
    status = Column(Enum(WorkOrderStatus), nullable=False, default=WorkOrderStatus.DRAFT)
    priority = Column(Enum(WorkOrderPriority), nullable=False, default=WorkOrderPriority.MEDIUM)

    # Scheduling (PLAN)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    assigned_track = Column(String(50), nullable=True)
    assigned_team = Column(String(100), nullable=True)

    # Actual execution (IST - authoritative for workshop)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)

    # Work details
    work_description = Column(String(1000), nullable=True)
    work_performed = Column(String(2000), nullable=True)
    findings = Column(String(2000), nullable=True)

    # Tasks associated with this work order
    tasks = Column(JSON, nullable=True)  # List of task types: ["HU", "INSPECTION"]

    # Cost tracking
    estimated_cost = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)

    # Metadata
    notes = Column(String(1000), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<WorkOrder(order_number='{self.order_number}', status='{self.status}')>"


class SyncConflict(Base):
    """Sync conflict tracking for offline-first system."""

    __tablename__ = "sync_conflicts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conflict_id = Column(String(50), unique=True, nullable=False, index=True)

    # Conflict details
    entity_type = Column(String(50), nullable=False)  # "work_order", "vehicle", etc.
    entity_id = Column(String(100), nullable=False)
    field_name = Column(String(100), nullable=False)

    # Values
    server_value = Column(JSON, nullable=True)
    client_value = Column(JSON, nullable=True)

    # Resolution
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_value = Column(JSON, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    # Context
    source_device = Column(String(100), nullable=True)
    source_role = Column(String(50), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SyncConflict(conflict_id='{self.conflict_id}', entity_type='{self.entity_type}')>"
