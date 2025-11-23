"""
Vehicle (Locomotive) model for fleet management.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from enum import Enum as PyEnum
from src.core.database import Base


class VehicleStatus(str, PyEnum):
    """Vehicle status enumeration."""
    AVAILABLE = "available"
    IN_SERVICE = "in_service"
    WORKSHOP_PLANNED = "workshop_planned"
    IN_WORKSHOP = "in_workshop"
    OUT_OF_SERVICE = "out_of_service"
    MAINTENANCE_DUE = "maintenance_due"
    RETIRED = "retired"


class VehicleType(str, PyEnum):
    """Vehicle type enumeration."""
    ELECTRIC = "electric"
    DIESEL = "diesel"
    HYBRID = "hybrid"


class Vehicle(Base):
    """Vehicle (Locomotive) model."""

    __tablename__ = "vehicles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "185123"
    model = Column(String(100), nullable=False)  # e.g., "Traxx F140 AC2"
    type = Column(Enum(VehicleType), nullable=False)
    manufacturer = Column(String(100), nullable=True)
    year = Column(Integer, nullable=True)
    status = Column(Enum(VehicleStatus), nullable=False, default=VehicleStatus.AVAILABLE)

    # Technical specifications
    max_speed_kmh = Column(Integer, nullable=True)
    power_kw = Column(Integer, nullable=True)
    weight_tons = Column(Float, nullable=True)

    # Operational data
    current_mileage_km = Column(Integer, nullable=False, default=0)
    total_operating_hours = Column(Integer, nullable=False, default=0)

    # Location
    current_location = Column(String(255), nullable=True)
    home_depot = Column(String(255), nullable=True)

    # Metadata
    notes = Column(String(1000), nullable=True)
    specifications = Column(JSON, nullable=True)  # Additional technical specs

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_service_date = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Vehicle(asset_id='{self.asset_id}', model='{self.model}', status='{self.status}')>"
