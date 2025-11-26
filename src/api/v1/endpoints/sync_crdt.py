"""CRDT Sync API endpoints - Local-first synchronization with CRDTs (WP18).

Provides HTTP endpoints for device registration, push/pull sync,
and CRDT-based conflict management.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....core.database import get_db
from ....models.railfleet.sync_device import SyncDevice, SyncSession
from ....models.railfleet.crdt_metadata import CRDTMetadataModel
from ....services.sync_engine import SyncEngine, SyncResult
from ....services.sync_queue import get_sync_queue, get_queue_manager
from ....config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class DeviceRegistrationRequest(BaseModel):
    """Request to register a new device."""

    device_id: str = Field(..., description="Unique device identifier")
    device_name: str = Field(..., description="Human-readable device name")
    device_type: str = Field(..., description="Type: mobile, tablet, desktop, workshop_terminal")
    platform: Optional[str] = Field(None, description="Platform: ios, android, windows, macos, linux")
    app_version: Optional[str] = Field(None, description="App version")
    capabilities: Dict[str, Any] = Field(default_factory=dict, description="Device capabilities")
    user_id: Optional[int] = Field(None, description="Associated user ID")


class DeviceRegistrationResponse(BaseModel):
    """Response from device registration."""

    device_id: str
    device_name: str
    registered_at: datetime
    is_active: bool


class SyncPushRequest(BaseModel):
    """Request to push local changes to server."""

    device_id: str = Field(..., description="Device identifier")
    states: List[Dict[str, Any]] = Field(..., description="CRDT states to push")


class SyncPullRequest(BaseModel):
    """Request to pull remote changes from server."""

    device_id: str = Field(..., description="Device identifier")
    since: Optional[datetime] = Field(None, description="Get changes since timestamp")
    entity_types: Optional[List[str]] = Field(None, description="Filter by entity types")


class SyncPullResponse(BaseModel):
    """Response from pull sync."""

    states: List[Dict[str, Any]] = Field(..., description="CRDT states from server")
    total_count: int
    has_more: bool = False


class SyncBidirectionalRequest(BaseModel):
    """Request for bidirectional sync (push + pull)."""

    device_id: str
    states: List[Dict[str, Any]] = Field(default_factory=list, description="Local states to push")
    since: Optional[datetime] = Field(None, description="Get changes since timestamp")
    entity_types: Optional[List[str]] = None


class SyncBidirectionalResponse(BaseModel):
    """Response from bidirectional sync."""

    push_result: Dict[str, Any]
    pull_states: List[Dict[str, Any]]
    pull_count: int
    session_id: str


class QueueStatsResponse(BaseModel):
    """Response with sync queue statistics."""

    device_id: str
    stats: Dict[str, int]


# ============================================================================
# Device Registration Endpoints
# ============================================================================


@router.post("/crdt/devices/register", response_model=DeviceRegistrationResponse)
def register_device(
    request: DeviceRegistrationRequest,
    db: Session = Depends(get_db),
):
    """Register a new device for CRDT synchronization.

    Args:
        request: Device registration details
        db: Database session

    Returns:
        Device registration confirmation
    """
    # Check if device already exists
    existing = (
        db.query(SyncDevice)
        .filter(SyncDevice.device_id == request.device_id)
        .first()
    )

    if existing:
        # Update existing device
        existing.device_name = request.device_name
        existing.device_type = request.device_type
        existing.platform = request.platform
        existing.app_version = request.app_version
        existing.capabilities = request.capabilities
        existing.user_id = request.user_id
        existing.is_active = True
        existing.updated_at = datetime.utcnow()
        db.commit()
        device = existing
        logger.info(f"Updated device registration: {request.device_id}")
    else:
        # Create new device
        device = SyncDevice(
            device_id=request.device_id,
            device_name=request.device_name,
            device_type=request.device_type,
            platform=request.platform,
            app_version=request.app_version,
            capabilities=request.capabilities,
            user_id=request.user_id,
        )
        db.add(device)
        db.commit()
        logger.info(f"Registered new device: {request.device_id}")

    return DeviceRegistrationResponse(
        device_id=device.device_id,
        device_name=device.device_name,
        registered_at=device.registered_at,
        is_active=device.is_active,
    )


@router.get("/crdt/devices/{device_id}")
def get_device(device_id: str, db: Session = Depends(get_db)):
    """Get device information.

    Args:
        device_id: Device identifier
        db: Database session

    Returns:
        Device details
    """
    device = (
        db.query(SyncDevice)
        .filter(SyncDevice.device_id == device_id)
        .first()
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found",
        )

    return {
        "device_id": device.device_id,
        "device_name": device.device_name,
        "device_type": device.device_type,
        "platform": device.platform,
        "app_version": device.app_version,
        "is_active": device.is_active,
        "is_offline": device.is_offline,
        "last_sync_at": device.last_sync_at,
        "registered_at": device.registered_at,
        "capabilities": device.capabilities,
    }


@router.put("/crdt/devices/{device_id}/status")
def update_device_status(
    device_id: str,
    is_offline: bool,
    db: Session = Depends(get_db),
):
    """Update device online/offline status.

    Args:
        device_id: Device identifier
        is_offline: Offline status
        db: Database session

    Returns:
        Updated status
    """
    device = (
        db.query(SyncDevice)
        .filter(SyncDevice.device_id == device_id)
        .first()
    )

    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Device {device_id} not found",
        )

    device.is_offline = is_offline
    device.updated_at = datetime.utcnow()
    db.commit()

    logger.info(f"Device {device_id} status: {'offline' if is_offline else 'online'}")

    return {
        "device_id": device.device_id,
        "is_offline": device.is_offline,
        "updated_at": device.updated_at,
    }


# ============================================================================
# Sync Endpoints
# ============================================================================


@router.post("/crdt/sync/push")
def sync_push(
    request: SyncPushRequest,
    db: Session = Depends(get_db),
):
    """Push local CRDT states to server.

    Args:
        request: Push sync request with states
        db: Database session

    Returns:
        Sync result with statistics
    """
    # Create sync session
    session = SyncSession(
        session_id=str(uuid4()),
        device_id=request.device_id,
        sync_type="push",
    )
    db.add(session)
    db.commit()

    try:
        # Sync states using engine
        engine = SyncEngine(db)
        result = engine.sync_from_remote(request.device_id, request.states)

        # Update device last_push_at
        device = (
            db.query(SyncDevice)
            .filter(SyncDevice.device_id == request.device_id)
            .first()
        )
        if device:
            device.last_push_at = datetime.utcnow()
            device.last_sync_at = datetime.utcnow()
            db.commit()

        # Update session
        session.entities_synced = result.entities_synced
        session.conflicts_resolved = result.conflicts_resolved
        session.operations_applied = result.operations_applied
        session.tombstones_processed = result.tombstones_processed
        session.errors_count = len(result.errors)
        session.errors = result.errors
        session.session_data = result.to_dict()
        session.completed_at = datetime.utcnow()
        session.status = "completed" if not result.errors else "failed"
        db.commit()

        logger.info(
            f"Push sync completed for {request.device_id}: "
            f"{result.entities_synced} entities"
        )

        return {
            "session_id": session.session_id,
            "result": result.to_dict(),
        }

    except Exception as e:
        session.status = "failed"
        session.errors = [str(e)]
        session.completed_at = datetime.utcnow()
        db.commit()
        logger.error(f"Push sync failed for {request.device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Push sync failed: {e}",
        )


@router.post("/crdt/sync/pull", response_model=SyncPullResponse)
def sync_pull(
    request: SyncPullRequest,
    db: Session = Depends(get_db),
):
    """Pull remote CRDT states from server.

    Args:
        request: Pull sync request
        db: Database session

    Returns:
        CRDT states from server
    """
    engine = SyncEngine(db)

    # Get changes since timestamp
    if request.since:
        states = engine.get_changes_since(request.device_id, request.since)
    else:
        states = engine.get_device_state(request.device_id, request.entity_types)

    # Convert to dict
    states_dict = [
        {
            "entity_type": state.entity_type,
            "entity_id": state.entity_id,
            "device_id": state.device_id,
            "vector_clock": state.vector_clock,
            "crdt_data": state.crdt_data,
            "tombstone": state.tombstone,
            "updated_at": state.updated_at.isoformat(),
        }
        for state in states
    ]

    # Update device last_pull_at
    device = (
        db.query(SyncDevice)
        .filter(SyncDevice.device_id == request.device_id)
        .first()
    )
    if device:
        device.last_pull_at = datetime.utcnow()
        device.last_sync_at = datetime.utcnow()
        db.commit()

    logger.info(f"Pull sync for {request.device_id}: {len(states_dict)} states")

    return SyncPullResponse(
        states=states_dict,
        total_count=len(states_dict),
    )


@router.post("/crdt/sync/bidirectional", response_model=SyncBidirectionalResponse)
def sync_bidirectional(
    request: SyncBidirectionalRequest,
    db: Session = Depends(get_db),
):
    """Perform bidirectional sync (push local + pull remote).

    Args:
        request: Bidirectional sync request
        db: Database session

    Returns:
        Combined push and pull results
    """
    session_id = str(uuid4())

    # Create sync session
    session = SyncSession(
        session_id=session_id,
        device_id=request.device_id,
        sync_type="bidirectional",
    )
    db.add(session)
    db.commit()

    try:
        engine = SyncEngine(db)

        # Push local states
        push_result = None
        if request.states:
            push_result = engine.sync_from_remote(request.device_id, request.states)

        # Pull remote states
        if request.since:
            pull_states = engine.get_changes_since(request.device_id, request.since)
        else:
            pull_states = engine.get_device_state(request.device_id, request.entity_types)

        # Convert to dict
        pull_states_dict = [
            {
                "entity_type": state.entity_type,
                "entity_id": state.entity_id,
                "device_id": state.device_id,
                "vector_clock": state.vector_clock,
                "crdt_data": state.crdt_data,
                "tombstone": state.tombstone,
                "updated_at": state.updated_at.isoformat(),
            }
            for state in pull_states
        ]

        # Update device
        device = (
            db.query(SyncDevice)
            .filter(SyncDevice.device_id == request.device_id)
            .first()
        )
        if device:
            device.last_sync_at = datetime.utcnow()
            device.last_push_at = datetime.utcnow()
            device.last_pull_at = datetime.utcnow()
            db.commit()

        # Update session
        if push_result:
            session.entities_synced = push_result.entities_synced
            session.conflicts_resolved = push_result.conflicts_resolved
            session.operations_applied = push_result.operations_applied
            session.tombstones_processed = push_result.tombstones_processed
        session.completed_at = datetime.utcnow()
        session.status = "completed"
        db.commit()

        logger.info(
            f"Bidirectional sync for {request.device_id}: "
            f"pushed {push_result.entities_synced if push_result else 0} entities, "
            f"pulled {len(pull_states_dict)} states"
        )

        return SyncBidirectionalResponse(
            push_result=push_result.to_dict() if push_result else {},
            pull_states=pull_states_dict,
            pull_count=len(pull_states_dict),
            session_id=session_id,
        )

    except Exception as e:
        session.status = "failed"
        session.errors = [str(e)]
        session.completed_at = datetime.utcnow()
        db.commit()
        logger.error(f"Bidirectional sync failed for {request.device_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bidirectional sync failed: {e}",
        )


# ============================================================================
# Queue Management Endpoints
# ============================================================================


@router.get("/crdt/queue/{device_id}/stats", response_model=QueueStatsResponse)
def get_queue_stats(device_id: str):
    """Get sync queue statistics for a device.

    Args:
        device_id: Device identifier

    Returns:
        Queue statistics
    """
    queue = get_sync_queue(device_id)
    stats = queue.get_queue_stats()

    return QueueStatsResponse(
        device_id=device_id,
        stats=stats,
    )


@router.get("/crdt/queue/{device_id}/pending")
def get_pending_operations(device_id: str, limit: Optional[int] = None):
    """Get pending operations for a device.

    Args:
        device_id: Device identifier
        limit: Maximum number of operations to return

    Returns:
        List of pending operations
    """
    queue = get_sync_queue(device_id)
    operations = queue.get_pending_operations(limit)

    return {
        "device_id": device_id,
        "operations": [op.to_dict() for op in operations],
        "count": len(operations),
    }


@router.post("/crdt/queue/{device_id}/clear-completed")
def clear_completed_operations(device_id: str):
    """Clear completed operations from queue.

    Args:
        device_id: Device identifier

    Returns:
        Number of operations cleared
    """
    queue = get_sync_queue(device_id)
    cleared = queue.clear_completed()

    logger.info(f"Cleared {cleared} completed operations for {device_id}")

    return {
        "device_id": device_id,
        "cleared_count": cleared,
    }


# ============================================================================
# Session History Endpoints
# ============================================================================


@router.get("/crdt/sessions/{device_id}")
def get_sync_sessions(
    device_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get sync session history for a device.

    Args:
        device_id: Device identifier
        limit: Maximum sessions to return
        db: Database session

    Returns:
        List of sync sessions
    """
    sessions = (
        db.query(SyncSession)
        .filter(SyncSession.device_id == device_id)
        .order_by(SyncSession.started_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "device_id": device_id,
        "sessions": [
            {
                "session_id": s.session_id,
                "sync_type": s.sync_type,
                "entities_synced": s.entities_synced,
                "conflicts_resolved": s.conflicts_resolved,
                "status": s.status,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
            }
            for s in sessions
        ],
        "count": len(sessions),
    }
