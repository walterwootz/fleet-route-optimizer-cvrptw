"""Projections API endpoints - Projection management and rebuild."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from ....core.database import get_db
from ....core.security import get_current_user
from ....models.railfleet.user import User
from ....services.projections.base import ProjectionManager
from ....services.projections import (
    VehicleProjection,
    MaintenanceProjection,
    InventoryProjection,
    ProcurementProjection,
    FinanceProjection,
)


router = APIRouter()


# Schemas

class ProjectionStatsResponse(BaseModel):
    """Projection statistics response."""
    total_projections: int
    projections: list


class RebuildResponse(BaseModel):
    """Projection rebuild response."""
    message: str
    projection: Optional[str] = None
    aggregate_id: Optional[str] = None


# Helper to initialize projection manager

def get_initialized_projection_manager(db: Session) -> ProjectionManager:
    """Get projection manager with all projections registered.

    Args:
        db: Database session

    Returns:
        Initialized projection manager
    """
    manager = ProjectionManager(db)

    # Register all projections
    manager.register(VehicleProjection(db))
    manager.register(MaintenanceProjection(db))
    manager.register(InventoryProjection(db))
    manager.register(ProcurementProjection(db))
    manager.register(FinanceProjection(db))

    return manager


# Endpoints

@router.get("/projections/stats", response_model=ProjectionStatsResponse, tags=["Projections"])
def get_projection_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about registered projections.

    Returns information about all projections including:
    - Total number of projections
    - Event types handled by each projection
    """
    manager = get_initialized_projection_manager(db)
    stats = manager.get_projection_stats()

    return ProjectionStatsResponse(**stats)


@router.post("/projections/rebuild", response_model=RebuildResponse, tags=["Projections"])
async def rebuild_all_projections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rebuild all projections from event history (admin only).

    This endpoint:
    - Replays all events through all projections
    - Rebuilds read models from scratch
    - Useful for fixing projection bugs or adding new projections

    **Warning:** This can be slow for large event stores.
    """
    # Check if user is admin
    if current_user.role not in ["SUPER_ADMIN", "FLEET_MANAGER"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    manager = get_initialized_projection_manager(db)

    try:
        manager.rebuild_all()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")

    return RebuildResponse(message="All projections rebuilt successfully")


@router.post("/projections/{projection_name}/rebuild", response_model=RebuildResponse, tags=["Projections"])
async def rebuild_projection(
    projection_name: str,
    aggregate_id: Optional[str] = Query(None, description="Rebuild for specific aggregate only"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rebuild a specific projection (admin only).

    Args:
        projection_name: Name of the projection to rebuild
        aggregate_id: Optional aggregate ID to rebuild for

    Valid projection names:
    - VehicleProjection
    - MaintenanceProjection
    - InventoryProjection
    - ProcurementProjection
    - FinanceProjection
    """
    # Check if user is admin
    if current_user.role not in ["SUPER_ADMIN", "FLEET_MANAGER"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    manager = get_initialized_projection_manager(db)

    try:
        manager.rebuild_projection(projection_name, aggregate_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rebuild failed: {str(e)}")

    return RebuildResponse(
        message=f"Projection {projection_name} rebuilt successfully",
        projection=projection_name,
        aggregate_id=aggregate_id
    )
