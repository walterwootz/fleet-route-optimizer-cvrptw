"""
HR service endpoints for staff and personnel management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from src.core.database import get_db
from src.models.railfleet.hr import Staff, StaffAssignment, StaffRole, StaffStatus
from src.api.schemas.hr import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
    StaffListResponse,
    StaffAssignmentCreate,
    StaffAssignmentUpdate,
    StaffAssignmentResponse,
    StaffAssignmentListResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/hr", tags=["HR"])


# Staff Management
@router.post("/staff", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    staff_data: StaffCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new staff member."""
    # Check if staff_id already exists
    if db.query(Staff).filter(Staff.staff_id == staff_data.staff_id).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Staff with staff_id '{staff_data.staff_id}' already exists",
        )

    # Convert workshop_id to UUID if provided
    workshop_id = UUID(staff_data.workshop_id) if staff_data.workshop_id else None

    new_staff = Staff(
        **staff_data.model_dump(exclude={"workshop_id"}),
        workshop_id=workshop_id,
    )
    db.add(new_staff)
    db.commit()
    db.refresh(new_staff)

    return StaffResponse(
        id=str(new_staff.id),
        **{k: v for k, v in new_staff.__dict__.items() if not k.startswith("_")},
    )


@router.get("/staff", response_model=StaffListResponse)
def list_staff(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    role: Optional[StaffRole] = None,
    status: Optional[StaffStatus] = None,
    is_available: Optional[bool] = None,
    workshop_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all staff with optional filtering."""
    query = db.query(Staff)

    if role:
        query = query.filter(Staff.role == role)

    if status:
        query = query.filter(Staff.status == status)

    if is_available is not None:
        query = query.filter(Staff.is_available == is_available)

    if workshop_id:
        query = query.filter(Staff.workshop_id == workshop_id)

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Staff.staff_id.ilike(search_pattern))
            | (Staff.first_name.ilike(search_pattern))
            | (Staff.last_name.ilike(search_pattern))
            | (Staff.employee_number.ilike(search_pattern))
        )

    total = query.count()
    staff = query.offset(skip).limit(limit).all()

    return StaffListResponse(
        total=total,
        staff=[
            StaffResponse(
                id=str(s.id),
                **{k: v for k, v in s.__dict__.items() if not k.startswith("_")},
            )
            for s in staff
        ],
    )


@router.get("/staff/{staff_id}", response_model=StaffResponse)
def get_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific staff member by ID."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff member {staff_id} not found",
        )

    return StaffResponse(
        id=str(staff.id),
        **{k: v for k, v in staff.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/staff/{staff_id}", response_model=StaffResponse)
def update_staff(
    staff_id: UUID,
    staff_update: StaffUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a staff member."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff member {staff_id} not found",
        )

    # Update fields
    update_data = staff_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "workshop_id" and value:
            value = UUID(value)
        setattr(staff, key, value)

    db.commit()
    db.refresh(staff)

    return StaffResponse(
        id=str(staff.id),
        **{k: v for k, v in staff.__dict__.items() if not k.startswith("_")},
    )


@router.delete("/staff/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a staff member."""
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff member {staff_id} not found",
        )

    db.delete(staff)
    db.commit()


# Staff Assignments
@router.post("/assignments", response_model=StaffAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_staff_assignment(
    assignment_data: StaffAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Assign staff to a work order or transfer."""
    try:
        staff_id = UUID(assignment_data.staff_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format for staff_id",
        )

    # Verify staff exists
    staff = db.query(Staff).filter(Staff.id == staff_id).first()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff member {staff_id} not found",
        )

    # Validate that assignment has either work_order_id or transfer_plan_id, but not both
    if assignment_data.work_order_id and assignment_data.transfer_plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment must be to either work_order OR transfer, not both",
        )

    if not assignment_data.work_order_id and not assignment_data.transfer_plan_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment must have either work_order_id or transfer_plan_id",
        )

    # Validate scheduled times
    if assignment_data.scheduled_end_ts <= assignment_data.scheduled_start_ts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scheduled end must be after scheduled start",
        )

    new_assignment = StaffAssignment(
        staff_id=staff_id,
        work_order_id=UUID(assignment_data.work_order_id) if assignment_data.work_order_id else None,
        transfer_plan_id=UUID(assignment_data.transfer_plan_id) if assignment_data.transfer_plan_id else None,
        scheduled_start_ts=assignment_data.scheduled_start_ts,
        scheduled_end_ts=assignment_data.scheduled_end_ts,
        role_on_assignment=assignment_data.role_on_assignment,
        status=assignment_data.status,
        planned_hours=assignment_data.planned_hours,
        assignment_notes=assignment_data.assignment_notes,
        created_by=current_user.id,
    )
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return StaffAssignmentResponse(
        id=str(new_assignment.id),
        **{k: v for k, v in new_assignment.__dict__.items() if not k.startswith("_")},
    )


@router.get("/assignments", response_model=StaffAssignmentListResponse)
def list_staff_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    staff_id: Optional[UUID] = None,
    work_order_id: Optional[UUID] = None,
    transfer_plan_id: Optional[UUID] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List staff assignments with optional filtering."""
    query = db.query(StaffAssignment)

    if staff_id:
        query = query.filter(StaffAssignment.staff_id == staff_id)

    if work_order_id:
        query = query.filter(StaffAssignment.work_order_id == work_order_id)

    if transfer_plan_id:
        query = query.filter(StaffAssignment.transfer_plan_id == transfer_plan_id)

    if status:
        query = query.filter(StaffAssignment.status == status)

    total = query.count()
    assignments = query.order_by(StaffAssignment.scheduled_start_ts.desc()).offset(skip).limit(limit).all()

    return StaffAssignmentListResponse(
        total=total,
        assignments=[
            StaffAssignmentResponse(
                id=str(a.id),
                **{k: v for k, v in a.__dict__.items() if not k.startswith("_")},
            )
            for a in assignments
        ],
    )


@router.get("/assignments/{assignment_id}", response_model=StaffAssignmentResponse)
def get_staff_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific staff assignment by ID."""
    assignment = db.query(StaffAssignment).filter(StaffAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff assignment {assignment_id} not found",
        )

    return StaffAssignmentResponse(
        id=str(assignment.id),
        **{k: v for k, v in assignment.__dict__.items() if not k.startswith("_")},
    )


@router.patch("/assignments/{assignment_id}", response_model=StaffAssignmentResponse)
def update_staff_assignment(
    assignment_id: UUID,
    assignment_update: StaffAssignmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a staff assignment."""
    assignment = db.query(StaffAssignment).filter(StaffAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff assignment {assignment_id} not found",
        )

    # Update fields
    update_data = assignment_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(assignment, key, value)

    db.commit()
    db.refresh(assignment)

    return StaffAssignmentResponse(
        id=str(assignment.id),
        **{k: v for k, v in assignment.__dict__.items() if not k.startswith("_")},
    )


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff_assignment(
    assignment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a staff assignment."""
    assignment = db.query(StaffAssignment).filter(StaffAssignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff assignment {assignment_id} not found",
        )

    db.delete(assignment)
    db.commit()
