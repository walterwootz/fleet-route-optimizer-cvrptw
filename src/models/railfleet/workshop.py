"""
Workshop model for managing maintenance facilities.
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from src.core.database import Base


class Workshop(Base):
    """Workshop/Maintenance facility model."""

    __tablename__ = "workshops"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., "WS-MUENCHEN"
    name = Column(String(200), nullable=False)
    location = Column(String(255), nullable=False)

    # Contact information
    contact_person = Column(String(200), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)

    # Capacity
    total_tracks = Column(Integer, nullable=False, default=1)
    available_tracks = Column(Integer, nullable=False, default=1)

    # Capabilities
    is_ecm_certified = Column(Boolean, default=False, nullable=False)
    specializations = Column(JSON, nullable=True)  # List of specializations
    supported_vehicle_types = Column(JSON, nullable=True)  # List of vehicle types

    # Rating
    rating = Column(Float, nullable=True)  # Average rating 0-5
    total_completed_orders = Column(Integer, default=0, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    notes = Column(String(1000), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Workshop(code='{self.code}', name='{self.name}')>"
