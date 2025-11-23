"""
Sync endpoints for offline-first synchronization.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional
from src.core.database import get_db
from src.services.railfleet.sync_service import SyncService
from src.api.schemas.sync import (
    SyncPushRequest,
    SyncPushResponse,
    SyncPullRequest,
    SyncPullResponse,
    ConflictResponse,
    ConflictResolveRequest,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/sync", tags=["Synchronization"])


@router.post("/push", response_model=SyncPushResponse)
def push_events(
    request: SyncPushRequest,
    x_device_id: Optional[str] = Header(None, alias="X-Device-Id"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Push offline changes to server.

    Client sends a list of events with field changes.
    Server processes each event, applies changes, or flags conflicts.
    """
    device_id = x_device_id or request.device_id

    if not device_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device ID is required (X-Device-Id header or request.device_id)",
        )

    sync_service = SyncService(db)

    # Process events
    result = sync_service.process_push_events(
        [event.model_dump() for event in request.events],
        device_id,
    )

    return SyncPushResponse(
        applied=result.get("applied", []),
        conflicts=result.get("conflicts", []),
        rejected=result.get("rejected", []),
        next_cursor=f"log-idx-{len(result.get('applied', []))}",
    )


@router.get("/pull", response_model=SyncPullResponse)
def pull_events(
    cursor: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Pull server changes since cursor.

    Returns events that happened on the server since the given cursor.
    """
    # In a real implementation, this would fetch events from an event log
    # For now, return empty list
    return SyncPullResponse(
        events=[],
        next_cursor=cursor,
    )


@router.get("/conflicts", response_model=list[ConflictResponse])
def list_conflicts(
    resolved: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all conflicts, optionally filtered by resolved status."""
    sync_service = SyncService(db)
    conflicts = sync_service.get_conflicts(resolved=resolved)

    return [
        ConflictResponse(
            id=str(c.id),
            conflict_id=c.conflict_id,
            entity_type=c.entity_type,
            entity_id=c.entity_id,
            field_name=c.field_name,
            server_value=c.server_value,
            client_value=c.client_value,
            is_resolved=c.is_resolved,
            created_at=c.created_at,
        )
        for c in conflicts
    ]


@router.post("/conflicts/{conflict_id}/resolve", response_model=ConflictResponse)
def resolve_conflict(
    conflict_id: str,
    request: ConflictResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resolve a conflict.

    - **resolution**: "server" (keep server value), "client" (use client value), or "custom"
    - **custom_value**: Value to use if resolution is "custom"
    """
    sync_service = SyncService(db)

    try:
        conflict = sync_service.resolve_conflict(
            conflict_id,
            request.resolution,
            request.custom_value,
            str(current_user.id),
        )

        return ConflictResponse(
            id=str(conflict.id),
            conflict_id=conflict.conflict_id,
            entity_type=conflict.entity_type,
            entity_id=conflict.entity_id,
            field_name=conflict.field_name,
            server_value=conflict.server_value,
            client_value=conflict.client_value,
            is_resolved=conflict.is_resolved,
            created_at=conflict.created_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
