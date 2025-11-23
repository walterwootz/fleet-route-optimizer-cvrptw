"""
Workshop management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID
from src.core.database import get_db
from src.models.railfleet.workshop import Workshop
from src.api.schemas.workshop import WorkshopCreate, WorkshopUpdate, WorkshopResponse
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/workshops", tags=["Workshops"])


@router.post("", response_model=WorkshopResponse, status_code=status.HTTP_201_CREATED)
def create_workshop(
    workshop_data: WorkshopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new workshop."""
    if db.query(Workshop).filter(Workshop.code == workshop_data.code).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Workshop with code '{workshop_data.code}' already exists",
        )

    new_workshop = Workshop(
        **workshop_data.model_dump(),
        available_tracks=workshop_data.total_tracks,
    )
    db.add(new_workshop)
    db.commit()
    db.refresh(new_workshop)
    return WorkshopResponse(id=str(new_workshop.id), **new_workshop.__dict__)


@router.get("", response_model=list[WorkshopResponse])
def list_workshops(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List workshops."""
    query = db.query(Workshop)
    if active_only:
        query = query.filter(Workshop.is_active == True)

    workshops = query.offset(skip).limit(limit).all()
    return [WorkshopResponse(id=str(w.id), **w.__dict__) for w in workshops]


@router.get("/{workshop_id}", response_model=WorkshopResponse)
def get_workshop(
    workshop_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get workshop by ID or code."""
    try:
        workshop = db.query(Workshop).filter(Workshop.id == UUID(workshop_id)).first()
    except ValueError:
        workshop = db.query(Workshop).filter(Workshop.code == workshop_id).first()

    if not workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workshop not found")

    return WorkshopResponse(id=str(workshop.id), **workshop.__dict__)


@router.patch("/{workshop_id}", response_model=WorkshopResponse)
def update_workshop(
    workshop_id: str,
    workshop_data: WorkshopUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update workshop."""
    try:
        workshop = db.query(Workshop).filter(Workshop.id == UUID(workshop_id)).first()
    except ValueError:
        workshop = db.query(Workshop).filter(Workshop.code == workshop_id).first()

    if not workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workshop not found")

    update_data = workshop_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workshop, field, value)

    db.commit()
    db.refresh(workshop)
    return WorkshopResponse(id=str(workshop.id), **workshop.__dict__)
