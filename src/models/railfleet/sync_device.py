"""Database models for device registration and sync tracking."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Index, text, JSON
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base


class SyncDevice(Base):
    """Device registration for local-first synchronization.

    Tracks devices that sync with the system, their capabilities,
    and last sync times.
    """

    __tablename__ = "sync_devices"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Device identification
    device_id = Column(String, nullable=False, unique=True, index=True)
    device_name = Column(String, nullable=False)
    device_type = Column(String, nullable=False)  # mobile, tablet, desktop, workshop_terminal

    # Device metadata
    platform = Column(String)  # ios, android, windows, macos, linux
    app_version = Column(String)
    last_ip_address = Column(String)

    # Sync tracking
    last_sync_at = Column(DateTime)
    last_push_at = Column(DateTime)
    last_pull_at = Column(DateTime)

    # Device status
    is_active = Column(Boolean, nullable=False, default=True)
    is_offline = Column(Boolean, nullable=False, default=False)

    # Device capabilities (JSONB for flexibility)
    capabilities = Column(JSONB, nullable=False, default=dict)

    # User association (optional - device may be shared)
    user_id = Column(Integer, nullable=True)

    # Timestamps
    registered_at = Column(
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

    # Indexes
    __table_args__ = (
        Index('ix_sync_devices_device_type', 'device_type'),
        Index('ix_sync_devices_is_active', 'is_active'),
        Index('ix_sync_devices_last_sync', 'last_sync_at'),
        Index('ix_sync_devices_user', 'user_id'),
    )

    def __repr__(self):
        return f"<SyncDevice {self.device_id} ({self.device_name})>"


class SyncSession(Base):
    """Sync session tracking for auditing and debugging.

    Tracks individual sync sessions with statistics and errors.
    """

    __tablename__ = "sync_sessions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Session identification
    session_id = Column(String, nullable=False, unique=True, index=True)
    device_id = Column(String, nullable=False, index=True)

    # Session type
    sync_type = Column(String, nullable=False)  # push, pull, bidirectional

    # Session statistics
    entities_synced = Column(Integer, nullable=False, default=0)
    conflicts_resolved = Column(Integer, nullable=False, default=0)
    operations_applied = Column(Integer, nullable=False, default=0)
    tombstones_processed = Column(Integer, nullable=False, default=0)
    errors_count = Column(Integer, nullable=False, default=0)

    # Session data (JSONB for flexibility)
    session_data = Column(JSONB, nullable=False, default=dict)
    errors = Column(JSONB, nullable=False, default=list)

    # Session timing
    started_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True
    )
    completed_at = Column(DateTime)

    # Session status
    status = Column(String, nullable=False, default="in_progress")  # in_progress, completed, failed

    # Indexes
    __table_args__ = (
        Index('ix_sync_sessions_device_started', 'device_id', 'started_at'),
        Index('ix_sync_sessions_status', 'status'),
        Index('ix_sync_sessions_type', 'sync_type'),
    )

    def __repr__(self):
        return f"<SyncSession {self.session_id} ({self.device_id})>"
