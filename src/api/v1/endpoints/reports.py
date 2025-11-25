"""
Reporting endpoints for KPIs and analytics.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, extract
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal
from src.core.database import get_db
from src.models.railfleet.vehicle import Vehicle, VehicleStatus
from src.models.railfleet.maintenance import WorkOrder, WorkOrderStatus
from src.models.railfleet.inventory import StockMove, Part
from src.models.railfleet.finance import Budget, InvoiceLine
from src.api.schemas.reports import (
    AvailabilityReportResponse,
    AvailabilityMetric,
    OnTimeRatioReportResponse,
    OnTimeMetric,
    PartsUsageReportResponse,
    PartsUsageMetric,
    CostReportResponse,
    CostMetric,
    DashboardSummary,
)
from src.api.v1.endpoints.auth import get_current_user
from src.models.railfleet.user import User

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/availability", response_model=AvailabilityReportResponse)
def get_availability_report(
    period: Optional[str] = Query(None, regex=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format (optional)"),
    vehicle_type: Optional[str] = Query(None, description="Filter by vehicle type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get vehicle availability report.

    **Metrics:**
    - Total vehicles
    - Available vehicles (status: AVAILABLE)
    - In service vehicles (status: IN_SERVICE)
    - In workshop vehicles (status: IN_WORKSHOP, WORKSHOP_PLANNED)
    - Out of service vehicles (status: OUT_OF_SERVICE, MAINTENANCE_DUE, RETIRED)
    - Availability % = (available + in_service) / total * 100

    **Query Parameters:**
    - period: YYYY-MM format (optional, for future time-based filtering)
    - vehicle_type: Filter by ELECTRIC, DIESEL, HYBRID
    """
    query = db.query(
        Vehicle.type,
        func.count(Vehicle.id).label('total'),
        func.sum(case((Vehicle.status == VehicleStatus.AVAILABLE.value, 1), else_=0)).label('available'),
        func.sum(case((Vehicle.status == VehicleStatus.IN_SERVICE.value, 1), else_=0)).label('in_service'),
        func.sum(case(
            (Vehicle.status.in_([VehicleStatus.IN_WORKSHOP.value, VehicleStatus.WORKSHOP_PLANNED.value]), 1),
            else_=0
        )).label('in_workshop'),
        func.sum(case(
            (Vehicle.status.in_([
                VehicleStatus.OUT_OF_SERVICE.value,
                VehicleStatus.MAINTENANCE_DUE.value,
                VehicleStatus.RETIRED.value
            ]), 1),
            else_=0
        )).label('out_of_service'),
    ).group_by(Vehicle.type)

    if vehicle_type:
        query = query.filter(Vehicle.type == vehicle_type)

    results = query.all()

    metrics = []
    total_vehicles = 0
    total_operational = 0

    for row in results:
        total = int(row.total)
        available = int(row.available)
        in_service = int(row.in_service)
        in_workshop = int(row.in_workshop)
        out_of_service = int(row.out_of_service)

        operational = available + in_service
        availability_pct = (operational / total * 100) if total > 0 else 0

        metrics.append(AvailabilityMetric(
            vehicle_type=row.type,
            total_vehicles=total,
            available_vehicles=available,
            in_service_vehicles=in_service,
            in_workshop_vehicles=in_workshop,
            out_of_service_vehicles=out_of_service,
            availability_pct=round(availability_pct, 2),
        ))

        total_vehicles += total
        total_operational += operational

    overall_availability_pct = (total_operational / total_vehicles * 100) if total_vehicles > 0 else 0

    return AvailabilityReportResponse(
        period=period or datetime.utcnow().strftime("%Y-%m"),
        metrics=metrics,
        overall_availability_pct=round(overall_availability_pct, 2),
        summary=f"{total_operational}/{total_vehicles} vehicles operational ({overall_availability_pct:.1f}% availability)",
    )


@router.get("/on_time_ratio", response_model=OnTimeRatioReportResponse)
def get_on_time_ratio_report(
    period: str = Query(..., regex=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format"),
    maintenance_type: Optional[str] = Query(None, description="Filter by maintenance type"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get on-time performance report for work orders.

    **Calculation:**
    - On-time: actual_end_date <= scheduled_end_date
    - Late: actual_end_date > scheduled_end_date
    - Only includes COMPLETED work orders
    - On-time ratio % = (on_time / total) * 100

    **Query Parameters:**
    - period: YYYY-MM format (required)
    - maintenance_type: Filter by maintenance type
    """
    # Parse period
    year, month = map(int, period.split('-'))

    # Query completed work orders in period
    query = db.query(
        WorkOrder.maintenance_type,
        func.count(WorkOrder.id).label('total'),
        func.sum(case(
            (WorkOrder.actual_end_date <= WorkOrder.scheduled_end_date, 1),
            else_=0
        )).label('on_time'),
        func.sum(case(
            (WorkOrder.actual_end_date > WorkOrder.scheduled_end_date, 1),
            else_=0
        )).label('late'),
        func.avg(
            extract('epoch', WorkOrder.actual_end_date - WorkOrder.scheduled_end_date) / 3600
        ).label('avg_delay_hours'),
    ).filter(
        WorkOrder.status == WorkOrderStatus.COMPLETED.value,
        WorkOrder.actual_end_date.isnot(None),
        extract('year', WorkOrder.actual_end_date) == year,
        extract('month', WorkOrder.actual_end_date) == month,
    ).group_by(WorkOrder.maintenance_type)

    if maintenance_type:
        query = query.filter(WorkOrder.maintenance_type == maintenance_type)

    results = query.all()

    metrics = []
    total_work_orders = 0
    total_on_time = 0

    for row in results:
        total = int(row.total)
        on_time = int(row.on_time)
        late = int(row.late)
        on_time_ratio_pct = (on_time / total * 100) if total > 0 else 0
        avg_delay_hours = float(row.avg_delay_hours) if row.avg_delay_hours and late > 0 else None

        metrics.append(OnTimeMetric(
            maintenance_type=row.maintenance_type,
            total_work_orders=total,
            on_time=on_time,
            late=late,
            on_time_ratio_pct=round(on_time_ratio_pct, 2),
            avg_delay_hours=round(avg_delay_hours, 2) if avg_delay_hours else None,
        ))

        total_work_orders += total
        total_on_time += on_time

    overall_on_time_ratio_pct = (total_on_time / total_work_orders * 100) if total_work_orders > 0 else 0

    return OnTimeRatioReportResponse(
        period=period,
        metrics=metrics,
        overall_on_time_ratio_pct=round(overall_on_time_ratio_pct, 2),
        summary=f"{total_on_time}/{total_work_orders} work orders completed on time ({overall_on_time_ratio_pct:.1f}%)",
    )


@router.get("/parts_usage", response_model=PartsUsageReportResponse)
def get_parts_usage_report(
    period: str = Query(..., regex=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format"),
    part_no: Optional[str] = Query(None, description="Filter by part number"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get parts usage report.

    **Metrics:**
    - Total quantity used per part
    - Total work orders using the part
    - Average quantity per work order
    - Total cost (quantity * unit_price)

    **Note:** Usage per 1,000km calculation requires vehicle mileage tracking,
    which is currently simplified in this implementation.

    **Query Parameters:**
    - period: YYYY-MM format (required)
    - part_no: Filter by specific part number
    """
    # Parse period
    year, month = map(int, period.split('-'))

    # Query stock moves with USAGE type
    query = db.query(
        StockMove.part_no,
        Part.name,
        func.sum(StockMove.quantity).label('total_quantity'),
        func.count(func.distinct(StockMove.work_order_id)).label('total_work_orders'),
        func.avg(StockMove.quantity).label('avg_quantity'),
        func.sum(StockMove.quantity * func.coalesce(StockMove.unit_price, 0)).label('total_cost'),
    ).join(
        Part, StockMove.part_no == Part.part_no
    ).filter(
        StockMove.move_type == "USAGE",
        extract('year', StockMove.performed_at) == year,
        extract('month', StockMove.performed_at) == month,
    ).group_by(StockMove.part_no, Part.name)

    if part_no:
        query = query.filter(StockMove.part_no == part_no)

    results = query.all()

    metrics = []
    total_parts_cost = Decimal(0)
    total_quantity = 0

    for row in results:
        total_qty = int(row.total_quantity)
        total_wo = int(row.total_work_orders)
        avg_qty = float(row.avg_quantity)
        cost = Decimal(str(row.total_cost)) if row.total_cost else Decimal(0)

        metrics.append(PartsUsageMetric(
            part_no=row.part_no,
            part_name=row.name,
            total_quantity_used=total_qty,
            total_work_orders=total_wo,
            avg_quantity_per_wo=round(avg_qty, 2),
            usage_per_1000km=None,  # Simplified: would require vehicle mileage tracking
            total_cost=cost,
        ))

        total_parts_cost += cost
        total_quantity += total_qty

    return PartsUsageReportResponse(
        period=period,
        metrics=metrics,
        total_parts_cost=total_parts_cost,
        total_quantity=total_quantity,
        summary=f"{total_quantity} parts used across {len(metrics)} different part numbers (total cost: {total_parts_cost:.2f})",
    )


@router.get("/costs", response_model=CostReportResponse)
def get_cost_report(
    period: str = Query(..., regex=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format"),
    cost_center: Optional[str] = Query(None, description="Filter by cost center"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get cost vs budget report.

    **Metrics:**
    - Planned budget
    - Actual cost
    - Variance (actual - planned)
    - Variance % = (variance / planned) * 100
    - Status: UNDER (<90%), ON_TRACK (90-110%), OVER (>110%)

    **Query Parameters:**
    - period: YYYY-MM format (required)
    - cost_center: Filter by cost center code
    """
    query = db.query(Budget).filter(Budget.period == period)

    if cost_center:
        query = query.filter(Budget.cost_center == cost_center)

    budgets = query.all()

    metrics = []
    warnings = []
    total_planned = Decimal(0)
    total_actual = Decimal(0)

    for budget in budgets:
        variance = budget.actual_amount - budget.planned_amount
        variance_pct = float((variance / budget.planned_amount * 100) if budget.planned_amount > 0 else 0)

        # Determine status
        if budget.planned_amount > 0:
            utilization = budget.actual_amount / budget.planned_amount
            if utilization < Decimal("0.90"):
                status = "UNDER"
            elif utilization <= Decimal("1.10"):
                status = "ON_TRACK"
            else:
                status = "OVER"
                warnings.append(
                    f"⚠️ Cost center '{budget.cost_center}' ({budget.category or 'N/A'}): "
                    f"{variance_pct:.1f}% over budget"
                )
        else:
            status = "N/A"

        metrics.append(CostMetric(
            cost_center=budget.cost_center,
            category=budget.category,
            planned_budget=budget.planned_amount,
            actual_cost=budget.actual_amount,
            variance=variance,
            variance_pct=round(variance_pct, 2),
            status=status,
        ))

        total_planned += budget.planned_amount
        total_actual += budget.actual_amount

    total_variance = total_actual - total_planned

    return CostReportResponse(
        period=period,
        metrics=metrics,
        total_planned=total_planned,
        total_actual=total_actual,
        total_variance=total_variance,
        warnings=warnings,
        summary=f"Total: {total_actual:.2f} / {total_planned:.2f} (variance: {total_variance:.2f})",
    )


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard_summary(
    period: str = Query(..., regex=r'^\d{4}-\d{2}$', description="Period in YYYY-MM format"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get overall dashboard summary combining all KPIs.

    **Aggregated Metrics:**
    - Vehicle availability %
    - On-time ratio %
    - Budget utilization %
    - Total work orders
    - Total parts cost
    - Alerts (budget overruns, low availability, etc.)

    **Query Parameters:**
    - period: YYYY-MM format (required)
    """
    # Get availability
    total_vehicles = db.query(func.count(Vehicle.id)).scalar()
    operational_vehicles = db.query(func.count(Vehicle.id)).filter(
        Vehicle.status.in_([VehicleStatus.AVAILABLE.value, VehicleStatus.IN_SERVICE.value])
    ).scalar()
    availability_pct = (operational_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0

    # Get on-time ratio
    year, month = map(int, period.split('-'))
    total_wo = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status == WorkOrderStatus.COMPLETED.value,
        WorkOrder.actual_end_date.isnot(None),
        extract('year', WorkOrder.actual_end_date) == year,
        extract('month', WorkOrder.actual_end_date) == month,
    ).scalar() or 0

    on_time_wo = db.query(func.count(WorkOrder.id)).filter(
        WorkOrder.status == WorkOrderStatus.COMPLETED.value,
        WorkOrder.actual_end_date.isnot(None),
        WorkOrder.actual_end_date <= WorkOrder.scheduled_end_date,
        extract('year', WorkOrder.actual_end_date) == year,
        extract('month', WorkOrder.actual_end_date) == month,
    ).scalar() or 0

    on_time_ratio_pct = (on_time_wo / total_wo * 100) if total_wo > 0 else 0

    # Get budget utilization
    budgets = db.query(
        func.sum(Budget.planned_amount).label('total_planned'),
        func.sum(Budget.actual_amount).label('total_actual')
    ).filter(Budget.period == period).first()

    total_planned = Decimal(str(budgets.total_planned)) if budgets and budgets.total_planned else Decimal(0)
    total_actual = Decimal(str(budgets.total_actual)) if budgets and budgets.total_actual else Decimal(0)
    budget_utilization_pct = float((total_actual / total_planned * 100) if total_planned > 0 else 0)

    # Get parts cost
    parts_cost_result = db.query(
        func.sum(StockMove.quantity * func.coalesce(StockMove.unit_price, 0))
    ).filter(
        StockMove.move_type == "USAGE",
        extract('year', StockMove.performed_at) == year,
        extract('month', StockMove.performed_at) == month,
    ).scalar()

    total_parts_cost = Decimal(str(parts_cost_result)) if parts_cost_result else Decimal(0)

    # Generate alerts
    alerts = []
    if availability_pct < 80:
        alerts.append(f"⚠️ Low vehicle availability: {availability_pct:.1f}%")
    if on_time_ratio_pct < 85:
        alerts.append(f"⚠️ Poor on-time performance: {on_time_ratio_pct:.1f}%")
    if budget_utilization_pct > 110:
        alerts.append(f"⚠️ Budget overrun: {budget_utilization_pct:.1f}% utilized")

    return DashboardSummary(
        period=period,
        availability_pct=round(availability_pct, 2),
        on_time_ratio_pct=round(on_time_ratio_pct, 2),
        budget_utilization_pct=round(budget_utilization_pct, 2),
        total_work_orders=total_wo,
        total_parts_cost=total_parts_cost,
        alerts=alerts,
    )
