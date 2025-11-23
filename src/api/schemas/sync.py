"""
Sync schemas for offline-first synchronization.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class FieldChange(BaseModel):
    """Field change in a sync event."""
    field: str
    value: Any


class SyncEvent(BaseModel):
    """Sync event from client."""
    id: str  # Client-generated event ID
    source_role: str  # Role of the user who made the change
    entity_type: str  # "work_order", "vehicle", etc.
    entity_id: str  # ID of the entity being changed
    field_changes: Dict[str, Any]  # Field name -> new value
    timestamp: Optional[datetime] = None


class SyncPushRequest(BaseModel):
    """Push request from client."""
    device_id: str
    events: List[SyncEvent]


class SyncPushResponse(BaseModel):
    """Push response to client."""
    applied: List[str]  # Event IDs that were applied
    conflicts: List[str]  # Event IDs that generated conflicts
    rejected: List[str]  # Event IDs that were rejected
    next_cursor: Optional[str] = None  # Cursor for next pull


class SyncPullRequest(BaseModel):
    """Pull request from client."""
    cursor: Optional[str] = None
    limit: int = Field(100, ge=1, le=1000)


class SyncPullResponse(BaseModel):
    """Pull response to client."""
    events: List[SyncEvent]
    next_cursor: Optional[str] = None


class ConflictResponse(BaseModel):
    """Conflict details."""
    id: str
    conflict_id: str
    entity_type: str
    entity_id: str
    field_name: str
    server_value: Any
    client_value: Any
    is_resolved: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ConflictResolveRequest(BaseModel):
    """Resolve conflict request."""
    resolution: str  # "server", "client", or "custom"
    custom_value: Optional[Any] = None
