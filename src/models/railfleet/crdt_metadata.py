"""Database models for CRDT metadata."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base


class CRDTMetadataModel(Base):
    """CRDT metadata table for tracking distributed operations.

    This table stores metadata for CRDT operations to enable
    conflict-free synchronization across devices.
    """

    __tablename__ = "crdt_metadata"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Entity identification
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)

    # Device identification
    device_id = Column(String, nullable=False, index=True)

    # Vector clock for causality
    vector_clock = Column(JSONB, nullable=False, default=dict)

    # CRDT state
    crdt_data = Column(JSONB, nullable=False, default=dict)

    # Deletion tracking
    tombstone = Column(Boolean, nullable=False, default=False)

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Indexes for efficient queries
    __table_args__ = (
        # Get latest state for an entity
        Index('ix_crdt_entity', 'entity_type', 'entity_id', 'device_id'),
        # Query by device
        Index('ix_crdt_device_updated', 'device_id', 'updated_at'),
        # Query active (non-tombstoned) entities
        Index('ix_crdt_active', 'entity_type', 'tombstone', 'updated_at'),
    )

    def __repr__(self):
        return f"<CRDTMetadata {self.entity_type}:{self.entity_id} device={self.device_id}>"


class CRDTOperation(Base):
    """CRDT operation log for auditing and debugging.

    Stores individual CRDT operations for debugging and analysis.
    """

    __tablename__ = "crdt_operations"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Operation identification
    operation_id = Column(String, nullable=False, unique=True, index=True)

    # Entity identification
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)

    # Device identification
    device_id = Column(String, nullable=False, index=True)

    # Operation details
    operation_type = Column(String, nullable=False)  # 'set', 'add', 'remove', 'increment', etc.
    operation_data = Column(JSONB, nullable=False, default=dict)

    # Vector clock at time of operation
    vector_clock = Column(JSONB, nullable=False, default=dict)

    # Timestamp
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True
    )

    # Indexes
    __table_args__ = (
        # Get operations for an entity
        Index('ix_crdt_ops_entity', 'entity_type', 'entity_id', 'created_at'),
        # Get operations by device
        Index('ix_crdt_ops_device', 'device_id', 'created_at'),
    )

    def __repr__(self):
        return f"<CRDTOperation {self.operation_type} {self.entity_type}:{self.entity_id}>"
