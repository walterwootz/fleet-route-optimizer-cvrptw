"""Database models for Event Sourcing."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index, text
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base


class Event(Base):
    """Event Store table.

    Stores all domain events in an append-only fashion.
    Events are immutable once written.
    """

    __tablename__ = "events"

    # Primary key
    event_id = Column(String, primary_key=True)

    # Event identity
    event_type = Column(String, nullable=False, index=True)
    event_version = Column(Integer, nullable=False, default=1)

    # Aggregate identity
    aggregate_id = Column(String, nullable=False, index=True)
    aggregate_type = Column(String, nullable=False, index=True)
    aggregate_version = Column(Integer, nullable=False)

    # Timestamps
    occurred_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Event data (JSONB for PostgreSQL performance)
    data = Column(JSONB, nullable=False, default=dict)
    metadata = Column(JSONB, nullable=False, default=dict)

    # Indexes for common queries
    __table_args__ = (
        # Ensure unique version per aggregate
        Index('ix_events_aggregate_version', 'aggregate_id', 'aggregate_version', unique=True),
        # Query by aggregate type and time
        Index('ix_events_aggregate_type_time', 'aggregate_type', 'occurred_at'),
        # Query by event type and time
        Index('ix_events_event_type_time', 'event_type', 'occurred_at'),
        # Composite index for common queries
        Index('ix_events_aggregate_id_version', 'aggregate_id', 'aggregate_version'),
    )

    def __repr__(self):
        return f"<Event {self.event_type} for {self.aggregate_type}:{self.aggregate_id} v{self.aggregate_version}>"


class EventSnapshot(Base):
    """Snapshot table for storing aggregate state.

    Snapshots are used to optimize aggregate reconstruction by
    avoiding replaying all events from the beginning.
    """

    __tablename__ = "event_snapshots"

    # Primary key
    snapshot_id = Column(String, primary_key=True)

    # Aggregate identity
    aggregate_id = Column(String, nullable=False, index=True)
    aggregate_type = Column(String, nullable=False, index=True)
    aggregate_version = Column(Integer, nullable=False)

    # Snapshot data
    state = Column(JSONB, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Indexes
    __table_args__ = (
        # Get latest snapshot for aggregate
        Index('ix_snapshots_aggregate_version', 'aggregate_id', 'aggregate_version'),
        # Query by aggregate type
        Index('ix_snapshots_aggregate_type', 'aggregate_type', 'created_at'),
    )

    def __repr__(self):
        return f"<Snapshot {self.aggregate_type}:{self.aggregate_id} v{self.aggregate_version}>"
