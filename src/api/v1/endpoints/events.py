"""Events API endpoints - Event Sourcing queries."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ....core.database import get_db
from .auth import get_current_user
from ....models.railfleet.user import User
from ....models.railfleet.events import Event
from ....services.event_store import EventStore
from pydantic import BaseModel


router = APIRouter()


# Schemas

class EventResponse(BaseModel):
    """Event response model."""
    event_id: str
    event_type: str
    event_version: int
    aggregate_id: str
    aggregate_type: str
    aggregate_version: int
    occurred_at: datetime
    data: dict
    metadata: dict

    class Config:
        orm_mode = True


class EventListResponse(BaseModel):
    """Event list response."""
    total: int
    events: List[EventResponse]


# Endpoints

@router.get("/events", response_model=EventListResponse, tags=["Events"])
def list_events(
    aggregate_type: Optional[str] = Query(None, description="Filter by aggregate type"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    since: Optional[datetime] = Query(None, description="Events after this timestamp"),
    until: Optional[datetime] = Query(None, description="Events before this timestamp"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List events with filters.

    Requires authentication. Returns events in reverse chronological order.
    """
    event_store = EventStore(db)

    events = event_store.get_all_events(
        aggregate_type=aggregate_type,
        event_type=event_type,
        since=since,
        until=until,
        limit=limit,
        offset=offset
    )

    # Count total (for pagination)
    total_query = db.query(Event)
    if aggregate_type:
        total_query = total_query.filter(Event.aggregate_type == aggregate_type)
    if event_type:
        total_query = total_query.filter(Event.event_type == event_type)
    if since:
        total_query = total_query.filter(Event.occurred_at >= since)
    if until:
        total_query = total_query.filter(Event.occurred_at <= until)

    total = total_query.count()

    return EventListResponse(
        total=total,
        events=[EventResponse.from_orm(event) for event in events]
    )


@router.get("/events/{aggregate_id}", response_model=EventListResponse, tags=["Events"])
def get_aggregate_events(
    aggregate_id: str,
    from_version: int = Query(0, ge=0, description="Start from this version"),
    to_version: Optional[int] = Query(None, description="End at this version"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all events for a specific aggregate.

    Returns events in chronological order (oldest first).
    """
    event_store = EventStore(db)

    events = event_store.get_events(
        aggregate_id=aggregate_id,
        from_version=from_version,
        to_version=to_version
    )

    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for aggregate {aggregate_id}")

    return EventListResponse(
        total=len(events),
        events=[EventResponse.from_orm(event) for event in events]
    )


@router.get("/events/{aggregate_id}/version", tags=["Events"])
def get_aggregate_version(
    aggregate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the latest version number for an aggregate."""
    event_store = EventStore(db)

    version = event_store.get_latest_version(aggregate_id)

    if version == 0:
        raise HTTPException(status_code=404, detail=f"Aggregate {aggregate_id} not found")

    return {
        "aggregate_id": aggregate_id,
        "latest_version": version
    }


@router.post("/events/replay/{aggregate_id}", tags=["Events"])
async def replay_aggregate_events(
    aggregate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Replay events for an aggregate (admin only).

    This endpoint is primarily for debugging and maintenance.
    It returns the sequence of events that would be used to reconstitute
    the aggregate state.
    """
    # Check if user is admin
    if current_user.role not in ["SUPER_ADMIN", "FLEET_MANAGER"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    event_store = EventStore(db)

    events = event_store.get_events(aggregate_id=aggregate_id)

    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for aggregate {aggregate_id}")

    return {
        "aggregate_id": aggregate_id,
        "total_events": len(events),
        "events": [EventResponse.from_orm(event) for event in events]
    }
