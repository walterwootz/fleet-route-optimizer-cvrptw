"""
Stock management endpoints for locations and moves.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional
from uuid import UUID
from src.core.database import get_db
from src.models.railfleet.inventory import Part, StockLocation, StockMove
from src.api.schemas.inventory import (
    StockLocationCreate,
    StockLocationUpdate,
    StockLocationResponse,
    StockLocationListResponse,
    StockMoveCreate,
    StockMoveResponse,
    StockMoveListResponse,
    StockOverviewResponse,
    StockOverviewItem,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/stock", tags=["Inventory - Stock"])


# ===== Stock Locations =====

@router.post("/locations", response_model=StockLocationResponse, status_code=status.HTTP_201_CREATED)
def create_location(
    location_data: StockLocationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new stock location.

    **Location Types:**
    - WORKSHOP: Workshop storage
    - CENTRAL: Central warehouse
    - TRAIN: Train/vehicle storage
    - CONSIGNMENT: Consignment stock
    """
    # Check if location_code already exists
    if db.query(StockLocation).filter(StockLocation.location_code == location_data.location_code).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location with code '{location_data.location_code}' already exists",
        )

    new_location = StockLocation(**location_data.model_dump())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)

    return StockLocationResponse(
        id=str(new_location.id),
        **{k: v for k, v in new_location.__dict__.items() if not k.startswith("_")},
    )


@router.get("/locations", response_model=StockLocationListResponse)
def list_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    location_type: Optional[str] = Query(None, description="Filter by type"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all stock locations with optional filtering.

    **Query Parameters:**
    - skip: Pagination offset
    - limit: Max results
    - location_type: Filter by WORKSHOP, CENTRAL, TRAIN, or CONSIGNMENT
    - is_active: Filter active/inactive locations
    """
    query = db.query(StockLocation).filter(StockLocation.is_active == is_active)

    if location_type:
        query = query.filter(StockLocation.location_type == location_type)

    total = query.count()
    locations = query.offset(skip).limit(limit).all()

    return StockLocationListResponse(
        total=total,
        locations=[
            StockLocationResponse(
                id=str(loc.id),
                **{k: v for k, v in loc.__dict__.items() if not k.startswith("_")},
            )
            for loc in locations
        ],
    )


@router.get("/locations/{location_id}", response_model=StockLocationResponse)
def get_location(
    location_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get location by ID or location_code."""
    try:
        location = db.query(StockLocation).filter(StockLocation.id == UUID(location_id)).first()
    except ValueError:
        location = db.query(StockLocation).filter(StockLocation.location_code == location_id).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location_id}' not found",
        )

    return StockLocationResponse(
        id=str(location.id),
        **{k: v for k, v in location.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/locations/{location_id}", response_model=StockLocationResponse)
def update_location(
    location_id: str,
    location_data: StockLocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update stock location (partial update)."""
    try:
        location = db.query(StockLocation).filter(StockLocation.id == UUID(location_id)).first()
    except ValueError:
        location = db.query(StockLocation).filter(StockLocation.location_code == location_id).first()

    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location '{location_id}' not found",
        )

    update_data = location_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(location, field, value)

    db.commit()
    db.refresh(location)

    return StockLocationResponse(
        id=str(location.id),
        **{k: v for k, v in location.__dict__.items() if not k.startswith("_")},
    )


# ===== Stock Moves =====

@router.post("/moves", response_model=StockMoveResponse, status_code=status.HTTP_201_CREATED)
def create_move(
    move_data: StockMoveCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new stock move.

    **Move Types:**
    - INCOMING: Goods receipt (wareneingang)
    - USAGE: Consumption in work order (verbauung)
    - TRANSFER: Transfer between locations (umbuchung)
    - WRITEOFF: Write-off/scrap (abschreibung)
    - ADJUSTMENT: Inventory adjustment

    **Note:** This creates an audit trail but does NOT automatically update part_inventory.current_stock.
    Stock updates should be managed via database triggers or separate business logic.
    """
    # Validate part exists
    part = db.query(Part).filter(Part.part_no == move_data.part_no).first()
    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part '{move_data.part_no}' not found",
        )

    # Validate locations if provided
    if move_data.from_location_id:
        try:
            from_loc = db.query(StockLocation).filter(StockLocation.id == UUID(move_data.from_location_id)).first()
            if not from_loc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"From location '{move_data.from_location_id}' not found",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid from_location_id UUID format",
            )

    if move_data.to_location_id:
        try:
            to_loc = db.query(StockLocation).filter(StockLocation.id == UUID(move_data.to_location_id)).first()
            if not to_loc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"To location '{move_data.to_location_id}' not found",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid to_location_id UUID format",
            )

    # Create move
    new_move = StockMove(
        **move_data.model_dump(),
        performed_by=current_user.id,
    )
    db.add(new_move)
    db.commit()
    db.refresh(new_move)

    return StockMoveResponse(
        id=str(new_move.id),
        performed_by=str(new_move.performed_by) if new_move.performed_by else None,
        **{k: v for k, v in new_move.__dict__.items() if not k.startswith("_") and k != "performed_by"},
    )


@router.get("/moves", response_model=StockMoveListResponse)
def list_moves(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    part_no: Optional[str] = Query(None, description="Filter by part number"),
    move_type: Optional[str] = Query(None, description="Filter by move type"),
    work_order_id: Optional[str] = Query(None, description="Filter by work order"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List stock moves with optional filtering.

    **Query Parameters:**
    - skip: Pagination offset
    - limit: Max results
    - part_no: Filter by part number
    - move_type: Filter by INCOMING, USAGE, TRANSFER, WRITEOFF, ADJUSTMENT
    - work_order_id: Filter by work order UUID
    """
    query = db.query(StockMove)

    if part_no:
        query = query.filter(StockMove.part_no == part_no)

    if move_type:
        query = query.filter(StockMove.move_type == move_type)

    if work_order_id:
        try:
            query = query.filter(StockMove.work_order_id == UUID(work_order_id))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid work_order_id UUID format",
            )

    # Order by most recent first
    query = query.order_by(StockMove.performed_at.desc())

    total = query.count()
    moves = query.offset(skip).limit(limit).all()

    return StockMoveListResponse(
        total=total,
        moves=[
            StockMoveResponse(
                id=str(m.id),
                performed_by=str(m.performed_by) if m.performed_by else None,
                **{k: v for k, v in m.__dict__.items() if not k.startswith("_") and k != "performed_by"},
            )
            for m in moves
        ],
    )


@router.get("/overview", response_model=StockOverviewResponse)
def get_stock_overview(
    part_no: Optional[str] = Query(None, description="Filter by part number"),
    location_code: Optional[str] = Query(None, description="Filter by location code"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get aggregated stock overview by part and location.

    **Aggregation Logic:**
    - Groups stock moves by part_no and location
    - Calculates net quantity (INCOMING/ADJUSTMENT adds, USAGE/WRITEOFF/TRANSFER subtracts)
    - Joins with part and location details

    **Query Parameters:**
    - part_no: Filter by specific part
    - location_code: Filter by specific location

    **Note:** This is a simplified aggregation. Production systems should use materialized views or dedicated stock tables.
    """
    # Build aggregation query
    # Net quantity = sum(INCOMING + ADJUSTMENT) - sum(USAGE + WRITEOFF + outbound TRANSFER)
    query = db.query(
        StockMove.part_no,
        Part.name.label("part_name"),
        Part.unit,
        Part.railway_class,
        StockLocation.location_code,
        StockLocation.name.label("location_name"),
        func.sum(
            case(
                (StockMove.move_type.in_(["INCOMING", "ADJUSTMENT"]), StockMove.quantity),
                (StockMove.move_type == "TRANSFER", case(
                    (StockMove.to_location_id == StockLocation.id, StockMove.quantity),
                    else_=-StockMove.quantity
                )),
                else_=-StockMove.quantity
            )
        ).label("quantity")
    ).join(
        Part, StockMove.part_no == Part.part_no
    ).outerjoin(
        StockLocation,
        (StockMove.to_location_id == StockLocation.id) | (StockMove.from_location_id == StockLocation.id)
    )

    # Apply filters
    if part_no:
        query = query.filter(StockMove.part_no == part_no)

    if location_code:
        query = query.filter(StockLocation.location_code == location_code)

    # Group by
    query = query.group_by(
        StockMove.part_no,
        Part.name,
        Part.unit,
        Part.railway_class,
        StockLocation.location_code,
        StockLocation.name,
    )

    results = query.all()

    items = [
        StockOverviewItem(
            part_no=r.part_no,
            part_name=r.part_name,
            location_code=r.location_code or "N/A",
            location_name=r.location_name or "No Location",
            quantity=int(r.quantity or 0),
            unit=r.unit,
            railway_class=r.railway_class,
        )
        for r in results
    ]

    return StockOverviewResponse(
        items=items,
        total_items=len(items),
    )
