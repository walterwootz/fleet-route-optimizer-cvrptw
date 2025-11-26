"""
Advanced Analytics API Endpoints

Provides REST API for analytics dashboards, metrics, and insights.

Endpoints:
- GET /analytics/dashboard/executive - Executive-level dashboard
- GET /analytics/dashboard/operations - Operations-level dashboard
- GET /analytics/dashboard/maintenance - Maintenance-focused dashboard
- GET /analytics/dashboard/inventory - Inventory-focused dashboard
- GET /analytics/metrics/summary - Summary of all key metrics
- GET /analytics/metrics/{metric_name} - Specific metric with trend
- GET /analytics/timeseries/{metric_name} - Time series data for metric
- GET /analytics/events/timeseries/{event_type} - Event count time series
- GET /analytics/kpis - All KPIs (availability, MTBF, MTTR, etc.)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from ....core.database import get_db
from src.services.analytics.metrics_calculator import MetricsCalculator
from src.services.analytics.dashboard_service import DashboardService


router = APIRouter(prefix="/analytics", tags=["analytics"])


# =============================================================================
# Dashboard Endpoints
# =============================================================================

@router.get("/dashboard/executive")
def get_executive_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get executive-level dashboard with high-level KPIs and trends.

    Returns:
        - Summary metrics
        - Trend charts (availability, costs)
        - Executive insights
        - 30-day period
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_executive_dashboard()


@router.get("/dashboard/operations")
def get_operations_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get operations-level dashboard with detailed operational metrics.

    Returns:
        - Active work orders breakdown
        - Vehicle status
        - Maintenance schedule
        - Operational charts
        - 7-day focus
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_operations_dashboard()


@router.get("/dashboard/maintenance")
def get_maintenance_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get maintenance-focused dashboard.

    Returns:
        - MTBF, MTTR metrics
        - Upcoming maintenance
        - Failure analysis
        - Maintenance backlog
        - Repair time distribution
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_maintenance_dashboard()


@router.get("/dashboard/inventory")
def get_inventory_dashboard(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get inventory-focused dashboard.

    Returns:
        - Turnover, stockout metrics
        - Low stock alerts
        - Stock level charts
        - ABC analysis
        - Usage trends
    """
    dashboard_service = DashboardService(db)
    return dashboard_service.get_inventory_dashboard()


# =============================================================================
# Metrics Endpoints
# =============================================================================

@router.get("/metrics/summary")
def get_metrics_summary(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get summary of all key metrics.

    Returns comprehensive dashboard summary with fleet, work order,
    inventory, and staff metrics.
    """
    calculator = MetricsCalculator(db)
    return calculator.get_dashboard_summary()


@router.get("/metrics/{metric_name}")
def get_metric(
    metric_name: str,
    vehicle_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific metric with current value and trend.

    Supported metrics:
    - fleet_availability: Fleet availability percentage
    - mtbf: Mean Time Between Failures
    - mttr: Mean Time To Repair
    - workorder_completion_rate: Work order completion rate
    - inventory_turnover: Inventory turnover rate
    - stockout_rate: Stockout percentage

    Query params:
    - vehicle_id: For vehicle-specific metrics (optional)
    - start_time: Period start (optional)
    - end_time: Period end (optional)
    """
    calculator = MetricsCalculator(db)

    if metric_name == "fleet_availability":
        metric = calculator.calculate_fleet_availability(start_time, end_time)
    elif metric_name == "mtbf":
        metric = calculator.calculate_mtbf(vehicle_id, start_time, end_time)
    elif metric_name == "mttr":
        metric = calculator.calculate_mttr(start_time, end_time)
    elif metric_name == "workorder_completion_rate":
        metric = calculator.calculate_workorder_completion_rate(start_time, end_time)
    elif metric_name == "inventory_turnover":
        metric = calculator.calculate_inventory_turnover(start_time, end_time)
    elif metric_name == "stockout_rate":
        metric = calculator.calculate_stockout_rate(start_time, end_time)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown metric: {metric_name}")

    return metric.to_dict()


@router.get("/kpis")
def get_all_kpis(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all Key Performance Indicators (KPIs).

    Returns current values for:
    - Fleet availability
    - MTBF (Mean Time Between Failures)
    - MTTR (Mean Time To Repair)
    - Work order completion rate
    - Inventory turnover
    - Stockout rate

    Each KPI includes:
    - Current value
    - Unit of measurement
    - Change percentage vs previous period
    - Trend direction (up/down/stable)
    """
    calculator = MetricsCalculator(db)

    kpis = {
        "fleet_availability": calculator.calculate_fleet_availability().to_dict(),
        "mtbf": calculator.calculate_mtbf().to_dict(),
        "mttr": calculator.calculate_mttr().to_dict(),
        "workorder_completion_rate": calculator.calculate_workorder_completion_rate().to_dict(),
        "inventory_turnover": calculator.calculate_inventory_turnover().to_dict(),
        "stockout_rate": calculator.calculate_stockout_rate().to_dict()
    }

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "kpis": kpis
    }


# =============================================================================
# Time Series Endpoints
# =============================================================================

@router.get("/timeseries/{metric_name}")
def get_metric_timeseries(
    metric_name: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    interval: str = Query("day", regex="^(hour|day|week|month)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get time series data for a metric.

    Supported metrics:
    - fleet_availability
    - mtbf
    - mttr
    - workorder_completion_rate

    Query params:
    - start_time: Period start (default: 30 days ago)
    - end_time: Period end (default: now)
    - interval: Data point interval (hour, day, week, month)

    Returns:
        List of data points with timestamp and value
    """
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)

    calculator = MetricsCalculator(db)

    try:
        data_points = calculator.generate_metric_time_series(
            metric_name,
            start_time,
            end_time,
            interval
        )

        return {
            "metric_name": metric_name,
            "interval": interval,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "data": [dp.to_dict() for dp in data_points]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events/timeseries/{event_type}")
def get_event_timeseries(
    event_type: str,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    interval: str = Query("day", regex="^(hour|day|week|month)$"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get time series data for event counts.

    Query params:
    - start_time: Period start (default: 30 days ago)
    - end_time: Period end (default: now)
    - interval: Data point interval (hour, day, week, month)

    Returns:
        List of data points with timestamp and event count
    """
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)

    calculator = MetricsCalculator(db)

    try:
        data_points = calculator.generate_event_time_series(
            event_type,
            start_time,
            end_time,
            interval
        )

        return {
            "event_type": event_type,
            "interval": interval,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "data": [dp.to_dict() for dp in data_points],
            "total_count": sum(dp.value for dp in data_points)
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# =============================================================================
# Custom Analytics Endpoints
# =============================================================================

@router.get("/fleet/availability-by-vehicle")
def get_fleet_availability_by_vehicle(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get availability metrics broken down by individual vehicle.

    Returns top/bottom vehicles by availability.
    """
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)

    calculator = MetricsCalculator(db)

    from src.models.railfleet.vehicle import Vehicle
    vehicles = db.query(Vehicle).limit(limit).all()

    vehicle_availability = []
    for vehicle in vehicles:
        mtbf = calculator.calculate_mtbf(vehicle.id, start_time, end_time)
        vehicle_availability.append({
            "vehicle_id": vehicle.id,
            "vehicle_number": vehicle.vehicle_number,
            "mtbf": mtbf.to_dict()
        })

    return {
        "period": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        "vehicles": vehicle_availability
    }


@router.get("/workorders/performance")
def get_workorder_performance(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive work order performance metrics.

    Returns:
    - Total work orders by status
    - Average completion time
    - Overdue count
    - Priority distribution
    """
    if not end_time:
        end_time = datetime.utcnow()
    if not start_time:
        start_time = end_time - timedelta(days=30)

    from src.models.railfleet.workorder import WorkOrder
    from sqlalchemy import func

    # Status distribution
    status_dist = db.query(
        WorkOrder.status,
        func.count(WorkOrder.id)
    ).filter(
        WorkOrder.created_at >= start_time,
        WorkOrder.created_at <= end_time
    ).group_by(WorkOrder.status).all()

    # Priority distribution
    priority_dist = db.query(
        WorkOrder.priority,
        func.count(WorkOrder.id)
    ).filter(
        WorkOrder.created_at >= start_time,
        WorkOrder.created_at <= end_time
    ).group_by(WorkOrder.priority).all()

    # Average completion time
    completed = db.query(WorkOrder).filter(
        WorkOrder.status == "completed",
        WorkOrder.created_at >= start_time,
        WorkOrder.updated_at <= end_time
    ).all()

    avg_completion_hours = 0
    if completed:
        total_hours = sum(
            (wo.updated_at - wo.created_at).total_seconds() / 3600
            for wo in completed if wo.created_at and wo.updated_at
        )
        avg_completion_hours = total_hours / len(completed)

    # Overdue count
    overdue_count = db.query(WorkOrder).filter(
        WorkOrder.status.in_(["pending", "in_progress"]),
        WorkOrder.created_at < end_time - timedelta(days=7)
    ).count()

    return {
        "period": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat()
        },
        "status_distribution": {status: count for status, count in status_dist},
        "priority_distribution": {priority: count for priority, count in priority_dist},
        "average_completion_hours": round(avg_completion_hours, 1),
        "overdue_count": overdue_count
    }


@router.get("/inventory/analysis")
def get_inventory_analysis(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get comprehensive inventory analysis.

    Returns:
    - Total items
    - Total value (estimated)
    - Low stock items
    - Overstock items
    - ABC classification (top items by value)
    """
    from src.models.railfleet.inventory import InventoryItem

    total_items = db.query(InventoryItem).count()

    # Low stock
    low_stock = db.query(InventoryItem).filter(
        InventoryItem.quantity < InventoryItem.reorder_point
    ).count()

    # Overstock (quantity > 3x reorder point)
    overstock = db.query(InventoryItem).filter(
        InventoryItem.quantity > InventoryItem.reorder_point * 3
    ).count()

    # Total value (estimated at $50/unit)
    all_items = db.query(InventoryItem).all()
    total_value = sum(item.quantity * 50 for item in all_items)

    # ABC analysis - top 10 by value
    item_values = [(item.part_number, item.quantity * 50) for item in all_items]
    item_values.sort(key=lambda x: x[1], reverse=True)
    top_10_items = [
        {"part_number": part, "estimated_value": value}
        for part, value in item_values[:10]
    ]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "total_items": total_items,
            "total_estimated_value": total_value,
            "low_stock_count": low_stock,
            "overstock_count": overstock
        },
        "abc_analysis": {
            "top_10_by_value": top_10_items
        }
    }


@router.get("/health")
def analytics_health_check() -> Dict[str, str]:
    """Health check endpoint for analytics service"""
    return {
        "status": "healthy",
        "service": "analytics",
        "version": "1.0.0"
    }
