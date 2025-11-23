"""
Parts management endpoints for inventory.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from src.core.database import get_db
from src.models.railfleet.inventory import Part
from src.api.schemas.inventory import (
    PartCreate,
    PartUpdate,
    PartResponse,
    PartListResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/parts", tags=["Inventory - Parts"])


@router.post("", response_model=PartResponse, status_code=status.HTTP_201_CREATED)
def create_part(
    part_data: PartCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new part.

    **Requires:** Authentication
    **Fields:**
    - part_no: Unique part number (required)
    - name: Part name (required)
    - railway_class: CRITICAL, STANDARD, or WEAR_PART
    - unit: Unit of measure (default: pc)
    - min_stock: Minimum stock level (default: 0)
    - current_stock: Initial stock quantity (default: 0)
    """
    # Check if part_no already exists
    if db.query(Part).filter(Part.part_no == part_data.part_no).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Part with part_no '{part_data.part_no}' already exists",
        )

    new_part = Part(**part_data.model_dump())
    db.add(new_part)
    db.commit()
    db.refresh(new_part)

    return PartResponse(
        id=str(new_part.id),
        **{k: v for k, v in new_part.__dict__.items() if not k.startswith("_")},
    )


@router.get("", response_model=PartListResponse)
def list_parts(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max records to return"),
    railway_class: Optional[str] = Query(None, description="Filter by railway class"),
    low_stock: bool = Query(False, description="Show only parts below min_stock"),
    search: Optional[str] = Query(None, description="Search by part_no or name"),
    is_active: bool = Query(True, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all parts with optional filtering.

    **Query Parameters:**
    - skip: Pagination offset (default: 0)
    - limit: Max results (default: 100, max: 1000)
    - railway_class: Filter by CRITICAL, STANDARD, or WEAR_PART
    - low_stock: Show only parts with current_stock <= min_stock
    - search: Search in part_no or name
    - is_active: Filter active/inactive parts (default: true)
    """
    query = db.query(Part).filter(Part.is_active == is_active)

    if railway_class:
        query = query.filter(Part.railway_class == railway_class)

    if low_stock:
        query = query.filter(Part.current_stock <= Part.min_stock)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Part.part_no.ilike(search_pattern)) | (Part.name.ilike(search_pattern))
        )

    total = query.count()
    parts = query.offset(skip).limit(limit).all()

    return PartListResponse(
        total=total,
        parts=[
            PartResponse(
                id=str(p.id),
                **{k: v for k, v in p.__dict__.items() if not k.startswith("_")},
            )
            for p in parts
        ],
    )


@router.get("/{part_id}", response_model=PartResponse)
def get_part(
    part_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get part by ID or part_no.

    **Parameters:**
    - part_id: Part UUID or part_no
    """
    # Try UUID first
    try:
        part = db.query(Part).filter(Part.id == UUID(part_id)).first()
    except ValueError:
        # Not a valid UUID, try part_no
        part = db.query(Part).filter(Part.part_no == part_id).first()

    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part '{part_id}' not found",
        )

    return PartResponse(
        id=str(part.id),
        **{k: v for k, v in part.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/{part_id}", response_model=PartResponse)
def update_part(
    part_id: str,
    part_data: PartUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update part (partial update).

    **Parameters:**
    - part_id: Part UUID or part_no
    **Note:** current_stock should be updated via stock moves, not directly
    """
    # Find part
    try:
        part = db.query(Part).filter(Part.id == UUID(part_id)).first()
    except ValueError:
        part = db.query(Part).filter(Part.part_no == part_id).first()

    if not part:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Part '{part_id}' not found",
        )

    # Update fields
    update_data = part_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(part, field, value)

    db.commit()
    db.refresh(part)

    return PartResponse(
        id=str(part.id),
        **{k: v for k, v in part.__dict__.items() if not k.startswith("_")},
    )
