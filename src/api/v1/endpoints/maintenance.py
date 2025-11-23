"""
Maintenance management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from uuid import UUID
from src.core.database import get_db
from src.models.railfleet.maintenance import MaintenanceTask, WorkOrder, WorkOrderStatus
from src.api.schemas.maintenance import (
    MaintenanceTaskCreate,
    MaintenanceTaskResponse,
    WorkOrderCreate,
    WorkOrderUpdate,
    WorkOrderResponse,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/maintenance", tags=["Maintenance"])


# Maintenance Tasks
@router.post("/tasks", response_model=MaintenanceTaskResponse, status_code=status.HTTP_201_CREATED)
def create_maintenance_task(
    task_data: MaintenanceTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new maintenance task."""
    new_task = MaintenanceTask(**task_data.model_dump())
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return MaintenanceTaskResponse(id=str(new_task.id), **new_task.__dict__)


@router.get("/tasks")
def list_maintenance_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    vehicle_id: Optional[str] = None,
    overdue_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List maintenance tasks with filtering."""
    query = db.query(MaintenanceTask)

    if vehicle_id:
        query = query.filter(MaintenanceTask.vehicle_id == vehicle_id)

    if overdue_only:
        query = query.filter(MaintenanceTask.is_overdue == True)

    tasks = query.offset(skip).limit(limit).all()
    return [MaintenanceTaskResponse(id=str(t.id), **t.__dict__) for t in tasks]


# Work Orders
@router.post("/orders", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(
    order_data: WorkOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new work order."""
    # Generate order number
    count = db.query(WorkOrder).count()
    order_number = f"WO-{datetime.utcnow().year}-{count+1:04d}"

    new_order = WorkOrder(
        order_number=order_number,
        **order_data.model_dump(),
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return WorkOrderResponse(id=str(new_order.id), **new_order.__dict__)


@router.get("/orders")
def list_work_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[WorkOrderStatus] = None,
    vehicle_id: Optional[str] = None,
    workshop_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List work orders with filtering."""
    query = db.query(WorkOrder)

    if status:
        query = query.filter(WorkOrder.status == status)
    if vehicle_id:
        query = query.filter(WorkOrder.vehicle_id == vehicle_id)
    if workshop_id:
        query = query.filter(WorkOrder.workshop_id == workshop_id)

    orders = query.offset(skip).limit(limit).all()
    return [WorkOrderResponse(id=str(o.id), **o.__dict__) for o in orders]


@router.patch("/orders/{order_id}", response_model=WorkOrderResponse)
def update_work_order(
    order_id: str,
    order_data: WorkOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update work order."""
    try:
        order = db.query(WorkOrder).filter(WorkOrder.id == UUID(order_id)).first()
    except ValueError:
        order = db.query(WorkOrder).filter(WorkOrder.order_number == order_id).first()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Work order not found")

    update_data = order_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)
    return WorkOrderResponse(id=str(order.id), **order.__dict__)
