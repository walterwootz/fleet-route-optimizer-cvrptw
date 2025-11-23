"""
Event log model for offline-first sync (append-only, WORM).
"""
from sqlalchemy import Column, String, BigInteger, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from src.core.database import Base


class EventLog(Base):
    """Event Log for offline-first sync (Write-Once-Read-Many)."""

    __tablename__ = "event_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(String(100), unique=True, nullable=False, index=True)

    # Entity information
    entity_type = Column(String(50), nullable=False)  # work_order, vehicle, transfer_plan, etc.
    entity_id = Column(String(100), nullable=False)
    event_type = Column(String(50), nullable=False)  # created, updated, deleted

    # Event payload
    payload_json = Column(JSON, nullable=False)  # Field changes

    # Actor information
    actor_id = Column(UUID(as_uuid=True), nullable=True)
    device_id = Column(String(100), nullable=True)

    # Timestamps
    source_ts = Column(DateTime, nullable=False)  # Client timestamp (may be backdated)
    server_received_ts = Column(DateTime, default=datetime.utcnow, nullable=False)  # Server timestamp (authoritative)

    # Idempotency
    idempotency_key = Column(String(100), nullable=True, unique=True)

    def __repr__(self):
        return f"<EventLog(id={self.id}, entity={self.entity_type}:{self.entity_id}, event={self.event_type})>"


# Indices are created in migration 05_event_log_conflicts.sql
