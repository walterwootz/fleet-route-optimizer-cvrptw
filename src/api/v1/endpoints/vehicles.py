"""
Vehicle management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from src.core.database import get_db
from src.models.railfleet.vehicle import Vehicle, VehicleStatus
from src.api.schemas.vehicle import (
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
    VehicleListResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
def create_vehicle(
    vehicle_data: VehicleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new vehicle."""
    # Check if asset_id already exists
    if db.query(Vehicle).filter(Vehicle.asset_id == vehicle_data.asset_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Vehicle with asset_id '{vehicle_data.asset_id}' already exists",
        )

    new_vehicle = Vehicle(**vehicle_data.model_dump())
    db.add(new_vehicle)
    db.commit()
    db.refresh(new_vehicle)

    return VehicleResponse(
        id=str(new_vehicle.id),
        **{k: v for k, v in new_vehicle.__dict__.items() if not k.startswith("_")},
    )


@router.get("", response_model=VehicleListResponse)
def list_vehicles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[VehicleStatus] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all vehicles with optional filtering."""
    query = db.query(Vehicle)

    if status:
        query = query.filter(Vehicle.status == status)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Vehicle.asset_id.ilike(search_pattern)) |
            (Vehicle.model.ilike(search_pattern)) |
            (Vehicle.manufacturer.ilike(search_pattern))
        )

    total = query.count()
    vehicles = query.offset(skip).limit(limit).all()

    return VehicleListResponse(
        total=total,
        vehicles=[
            VehicleResponse(
                id=str(v.id),
                **{k: val for k, val in v.__dict__.items() if not k.startswith("_")},
            )
            for v in vehicles
        ],
    )


@router.get("/{vehicle_id}", response_model=VehicleResponse)
def get_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get vehicle by ID or asset_id."""
    # Try UUID first
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.id == UUID(vehicle_id)).first()
    except ValueError:
        # Not a valid UUID, try asset_id
        vehicle = db.query(Vehicle).filter(Vehicle.asset_id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    return VehicleResponse(
        id=str(vehicle.id),
        **{k: v for k, v in vehicle.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/{vehicle_id}", response_model=VehicleResponse)
def update_vehicle(
    vehicle_id: str,
    vehicle_data: VehicleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update vehicle (partial updates allowed)."""
    # Find vehicle
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.id == UUID(vehicle_id)).first()
    except ValueError:
        vehicle = db.query(Vehicle).filter(Vehicle.asset_id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    # Validate mileage only increases
    if vehicle_data.current_mileage_km is not None:
        if vehicle_data.current_mileage_km < vehicle.current_mileage_km:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mileage can only increase",
            )

    # Update fields
    update_data = vehicle_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vehicle, field, value)

    db.commit()
    db.refresh(vehicle)

    return VehicleResponse(
        id=str(vehicle.id),
        **{k: v for k, v in vehicle.__dict__.items() if not k.startswith("_")},
    )


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete vehicle."""
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.id == UUID(vehicle_id)).first()
    except ValueError:
        vehicle = db.query(Vehicle).filter(Vehicle.asset_id == vehicle_id).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found",
        )

    db.delete(vehicle)
    db.commit()
    return None
