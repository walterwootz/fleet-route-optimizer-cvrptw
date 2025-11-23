"""
Transfer service endpoints for locomotive movement planning.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from src.core.database import get_db
from src.models.railfleet.transfer import TransferPlan, TransferAssignment, TransferStatus
from src.api.schemas.transfer import (
    TransferPlanCreate,
    TransferPlanUpdate,
    TransferPlanResponse,
    TransferPlanListResponse,
    TransferAssignmentCreate,
    TransferAssignmentUpdate,
    TransferAssignmentResponse,
    TransferAssignmentListResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/transfer", tags=["Transfer"])


# Transfer Plans
@router.post("/plans", response_model=TransferPlanResponse, status_code=status.HTTP_201_CREATED)
def create_transfer_plan(
    plan_data: TransferPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new transfer plan."""
    # Check if plan_id already exists
    if db.query(TransferPlan).filter(TransferPlan.plan_id == plan_data.plan_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transfer plan with plan_id '{plan_data.plan_id}' already exists",
        )

    # Validate scheduled times
    if plan_data.scheduled_arrival_ts <= plan_data.scheduled_departure_ts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled arrival must be after scheduled departure",
        )

    new_plan = TransferPlan(**plan_data.model_dump(), created_by=current_user.id)
    db.add(new_plan)
    db.commit()
    db.refresh(new_plan)

    return TransferPlanResponse(
        id=str(new_plan.id),
        **{k: v for k, v in new_plan.__dict__.items() if not k.startswith("_")},
    )


@router.get("/plans", response_model=TransferPlanListResponse)
def list_transfer_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TransferStatus] = None,
    from_location: Optional[str] = None,
    to_location: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all transfer plans with optional filtering."""
    query = db.query(TransferPlan)

    if status:
        query = query.filter(TransferPlan.status == status)

    if from_location:
        query = query.filter(TransferPlan.from_location.ilike(f"%{from_location}%"))

    if to_location:
        query = query.filter(TransferPlan.to_location.ilike(f"%{to_location}%"))

    total = query.count()
    plans = query.order_by(TransferPlan.scheduled_departure_ts.desc()).offset(skip).limit(limit).all()

    return TransferPlanListResponse(
        total=total,
        plans=[
            TransferPlanResponse(
                id=str(p.id),
                **{k: v for k, v in p.__dict__.items() if not k.startswith("_")},
            )
            for p in plans
        ],
    )


@router.get("/plans/{plan_id}", response_model=TransferPlanResponse)
def get_transfer_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific transfer plan by ID."""
    plan = db.query(TransferPlan).filter(TransferPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer plan {plan_id} not found",
        )

    return TransferPlanResponse(
        id=str(plan.id),
        **{k: v for k, v in plan.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/plans/{plan_id}", response_model=TransferPlanResponse)
def update_transfer_plan(
    plan_id: UUID,
    plan_update: TransferPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a transfer plan."""
    plan = db.query(TransferPlan).filter(TransferPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer plan {plan_id} not found",
        )

    # Update fields
    update_data = plan_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    db.commit()
    db.refresh(plan)

    return TransferPlanResponse(
        id=str(plan.id),
        **{k: v for k, v in plan.__dict__.items() if not k.startswith("_")},
    )


@router.delete("/plans/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transfer_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a transfer plan."""
    plan = db.query(TransferPlan).filter(TransferPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer plan {plan_id} not found",
        )

    db.delete(plan)
    db.commit()


# Transfer Assignments
@router.post("/assignments", response_model=TransferAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_transfer_assignment(
    assignment_data: TransferAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign a vehicle to a transfer plan."""
    try:
        transfer_plan_id = UUID(assignment_data.transfer_plan_id)
        vehicle_id = UUID(assignment_data.vehicle_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for transfer_plan_id or vehicle_id",
        )

    # Verify plan exists
    plan = db.query(TransferPlan).filter(TransferPlan.id == transfer_plan_id).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer plan {transfer_plan_id} not found",
        )

    new_assignment = TransferAssignment(
        transfer_plan_id=transfer_plan_id,
        vehicle_id=vehicle_id,
        position_in_convoy=assignment_data.position_in_convoy,
        driver_id=UUID(assignment_data.driver_id) if assignment_data.driver_id else None,
        confirmation_notes=assignment_data.confirmation_notes,
        assigned_by=current_user.id,
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return TransferAssignmentResponse(
        id=str(new_assignment.id),
        **{k: v for k, v in new_assignment.__dict__.items() if not k.startswith("_")},
    )


@router.get("/assignments", response_model=TransferAssignmentListResponse)
def list_transfer_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    transfer_plan_id: Optional[UUID] = None,
    vehicle_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List transfer assignments with optional filtering."""
    query = db.query(TransferAssignment)

    if transfer_plan_id:
        query = query.filter(TransferAssignment.transfer_plan_id == transfer_plan_id)

    if vehicle_id:
        query = query.filter(TransferAssignment.vehicle_id == vehicle_id)

    total = query.count()
    assignments = query.offset(skip).limit(limit).all()

    return TransferAssignmentListResponse(
        total=total,
        assignments=[
            TransferAssignmentResponse(
                id=str(a.id),
                **{k: v for k, v in a.__dict__.items() if not k.startswith("_")},
            )
            for a in assignments
        ],
    )


@router.patch("/assignments/{assignment_id}", response_model=TransferAssignmentResponse)
def update_transfer_assignment(
    assignment_id: UUID,
    assignment_update: TransferAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a transfer assignment."""
    assignment = db.query(TransferAssignment).filter(TransferAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transfer assignment {assignment_id} not found",
        )

    # Update fields
    update_data = assignment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "driver_id" and value:
            value = UUID(value)
        setattr(assignment, key, value)

    db.commit()
    db.refresh(assignment)

    return TransferAssignmentResponse(
        id=str(assignment.id),
        **{k: v for k, v in assignment.__dict__.items() if not k.startswith("_")},
    )
