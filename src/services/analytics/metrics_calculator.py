"""
Advanced Analytics - Real-time Metrics Calculator

Calculates real-time metrics from event sourcing data for dashboard visualization.
Supports time-based aggregations, KPIs, and trend analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from collections import defaultdict
import statistics

from src.models.railfleet.events import Event
from src.models.railfleet.vehicle import Vehicle
from src.models.railfleet.maintenance import WorkOrder
from src.models.railfleet.inventory import Part
from src.models.railfleet.hr import Staff


class MetricValue:
    """Represents a calculated metric with metadata"""

    def __init__(
        self,
        name: str,
        value: float,
        unit: str,
        timestamp: datetime,
        change_percentage: Optional[float] = None,
        trend: Optional[str] = None  # 'up', 'down', 'stable'
    ):
        self.name = name
        self.value = value
        self.unit = unit
        self.timestamp = timestamp
        self.change_percentage = change_percentage
        self.trend = trend

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "change_percentage": self.change_percentage,
            "trend": self.trend
        }


class TimeSeriesDataPoint:
    """Single data point in a time series"""

    def __init__(self, timestamp: datetime, value: float, label: Optional[str] = None):
        self.timestamp = timestamp
        self.value = value
        self.label = label

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value
        }
        if self.label:
            result["label"] = self.label
        return result


class MetricsCalculator:
    """
    Calculates real-time metrics from event sourcing data.

    Supports:
    - KPI calculations (fleet availability, MTBF, MTTR)
    - Time series generation
    - Trend analysis
    - Comparative metrics (current vs previous period)
    """

    def __init__(self, db: Session):
        self.db = db

    # =============================================================================
    # Fleet Metrics
    # =============================================================================

    def calculate_fleet_availability(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricValue:
        """
        Calculate fleet availability percentage.

        Availability = (Total Time - Downtime) / Total Time * 100
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=30)

        # Get all vehicles
        total_vehicles = self.db.query(func.count(Vehicle.id)).scalar() or 0

        if total_vehicles == 0:
            return MetricValue("fleet_availability", 0.0, "%", end_time, 0.0, "stable")

        # Get maintenance events in period
        maintenance_events = self.db.query(Event).filter(
            Event.event_type == "VehicleMaintenanceScheduled",
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        ).all()

        # Calculate downtime hours
        total_downtime_hours = 0
        for event in maintenance_events:
            # Estimate 2 days downtime per maintenance event
            total_downtime_hours += 48

        # Calculate total available hours
        period_hours = (end_time - start_time).total_seconds() / 3600
        total_hours = period_hours * total_vehicles

        if total_hours == 0:
            availability = 100.0
        else:
            availability = max(0, (total_hours - total_downtime_hours) / total_hours * 100)

        # Calculate trend (compare with previous period)
        prev_start = start_time - (end_time - start_time)
        prev_metric = self.calculate_fleet_availability(prev_start, start_time)
        change_pct = availability - prev_metric.value
        trend = "up" if change_pct > 0.5 else ("down" if change_pct < -0.5 else "stable")

        return MetricValue(
            "fleet_availability",
            round(availability, 2),
            "%",
            end_time,
            round(change_pct, 2),
            trend
        )

    def calculate_mtbf(
        self,
        vehicle_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricValue:
        """
        Calculate Mean Time Between Failures (MTBF) in hours.

        MTBF = Total Operating Time / Number of Failures
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=90)

        # Query failure events
        query = self.db.query(Event).filter(
            Event.event_type == "VehicleBreakdownReported",
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        )

        if vehicle_id:
            query = query.filter(Event.aggregate_id == vehicle_id)

        failure_count = query.count()

        if failure_count == 0:
            # No failures - excellent!
            mtbf = (end_time - start_time).total_seconds() / 3600
        else:
            # Calculate operating time (exclude maintenance downtime)
            period_hours = (end_time - start_time).total_seconds() / 3600
            mtbf = period_hours / failure_count

        # Calculate trend
        prev_start = start_time - (end_time - start_time)
        prev_metric = self.calculate_mtbf(vehicle_id, prev_start, start_time)
        change_pct = ((mtbf - prev_metric.value) / prev_metric.value * 100) if prev_metric.value > 0 else 0
        trend = "up" if change_pct > 5 else ("down" if change_pct < -5 else "stable")

        return MetricValue(
            "mtbf",
            round(mtbf, 1),
            "hours",
            end_time,
            round(change_pct, 2),
            trend
        )

    def calculate_mttr(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricValue:
        """
        Calculate Mean Time To Repair (MTTR) in hours.

        MTTR = Total Repair Time / Number of Repairs
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=90)

        # Get completed work orders
        completed_orders = self.db.query(WorkOrder).filter(
            WorkOrder.status == "completed",
            WorkOrder.updated_at >= start_time,
            WorkOrder.updated_at <= end_time
        ).all()

        if not completed_orders:
            return MetricValue("mttr", 0.0, "hours", end_time, 0.0, "stable")

        # Calculate repair times
        repair_times = []
        for order in completed_orders:
            if order.created_at and order.updated_at:
                repair_time = (order.updated_at - order.created_at).total_seconds() / 3600
                repair_times.append(repair_time)

        if not repair_times:
            return MetricValue("mttr", 0.0, "hours", end_time, 0.0, "stable")

        mttr = statistics.mean(repair_times)

        # Calculate trend
        prev_start = start_time - (end_time - start_time)
        prev_metric = self.calculate_mttr(prev_start, start_time)
        change_pct = ((mttr - prev_metric.value) / prev_metric.value * 100) if prev_metric.value > 0 else 0
        trend = "down" if change_pct < -5 else ("up" if change_pct > 5 else "stable")  # Down is good for MTTR

        return MetricValue(
            "mttr",
            round(mttr, 1),
            "hours",
            end_time,
            round(change_pct, 2),
            trend
        )

    # =============================================================================
    # Work Order Metrics
    # =============================================================================

    def calculate_workorder_completion_rate(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricValue:
        """Calculate percentage of work orders completed on time"""
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=30)

        # Get all completed work orders
        completed = self.db.query(WorkOrder).filter(
            WorkOrder.status == "completed",
            WorkOrder.updated_at >= start_time,
            WorkOrder.updated_at <= end_time
        ).count()

        # Get overdue work orders
        overdue = self.db.query(WorkOrder).filter(
            WorkOrder.status.in_(["pending", "in_progress"]),
            WorkOrder.created_at < end_time - timedelta(days=7)  # Overdue if > 7 days old
        ).count()

        total = completed + overdue

        if total == 0:
            rate = 100.0
        else:
            rate = (completed / total) * 100

        # Calculate trend
        prev_start = start_time - (end_time - start_time)
        prev_metric = self.calculate_workorder_completion_rate(prev_start, start_time)
        change_pct = rate - prev_metric.value
        trend = "up" if change_pct > 2 else ("down" if change_pct < -2 else "stable")

        return MetricValue(
            "workorder_completion_rate",
            round(rate, 2),
            "%",
            end_time,
            round(change_pct, 2),
            trend
        )

    # =============================================================================
    # Inventory Metrics
    # =============================================================================

    def calculate_inventory_turnover(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricValue:
        """
        Calculate inventory turnover rate.

        Turnover = Cost of Goods Used / Average Inventory Value
        """
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=90)

        # Get inventory usage events
        usage_events = self.db.query(Event).filter(
            Event.event_type == "InventoryItemUsed",
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        ).all()

        total_used_value = 0
        for event in usage_events:
            quantity = event.data.get("quantity", 0)
            # Estimate value (would need actual part costs)
            total_used_value += quantity * 50  # $50 average part cost

        # Get average inventory value
        items = self.db.query(InventoryItem).all()
        total_inventory_value = sum(item.quantity * 50 for item in items)  # $50 average

        if total_inventory_value == 0:
            turnover = 0.0
        else:
            period_months = (end_time - start_time).days / 30
            turnover = (total_used_value / total_inventory_value) / period_months if period_months > 0 else 0

        # Calculate trend
        prev_start = start_time - (end_time - start_time)
        prev_metric = self.calculate_inventory_turnover(prev_start, start_time)
        change_pct = ((turnover - prev_metric.value) / prev_metric.value * 100) if prev_metric.value > 0 else 0
        trend = "up" if change_pct > 5 else ("down" if change_pct < -5 else "stable")

        return MetricValue(
            "inventory_turnover",
            round(turnover, 2),
            "per month",
            end_time,
            round(change_pct, 2),
            trend
        )

    def calculate_stockout_rate(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> MetricValue:
        """Calculate percentage of time items are out of stock"""
        if not end_time:
            end_time = datetime.utcnow()
        if not start_time:
            start_time = end_time - timedelta(days=30)

        # Get low stock events
        low_stock_events = self.db.query(Event).filter(
            Event.event_type == "InventoryLowStockAlert",
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        ).count()

        # Get total inventory items
        total_items = self.db.query(InventoryItem).count()

        if total_items == 0:
            rate = 0.0
        else:
            # Approximate stockout rate
            rate = min(100, (low_stock_events / total_items) * 10)

        # Calculate trend
        prev_start = start_time - (end_time - start_time)
        prev_metric = self.calculate_stockout_rate(prev_start, start_time)
        change_pct = rate - prev_metric.value
        trend = "down" if change_pct < -1 else ("up" if change_pct > 1 else "stable")  # Down is good

        return MetricValue(
            "stockout_rate",
            round(rate, 2),
            "%",
            end_time,
            round(change_pct, 2),
            trend
        )

    # =============================================================================
    # Time Series Generation
    # =============================================================================

    def generate_event_time_series(
        self,
        event_type: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "day"  # 'hour', 'day', 'week', 'month'
    ) -> List[TimeSeriesDataPoint]:
        """Generate time series data for event counts"""

        events = self.db.query(Event).filter(
            Event.event_type == event_type,
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        ).order_by(Event.occurred_at).all()

        # Group by interval
        interval_data = defaultdict(int)

        for event in events:
            if interval == "hour":
                key = event.occurred_at.replace(minute=0, second=0, microsecond=0)
            elif interval == "day":
                key = event.occurred_at.replace(hour=0, minute=0, second=0, microsecond=0)
            elif interval == "week":
                key = event.occurred_at - timedelta(days=event.occurred_at.weekday())
                key = key.replace(hour=0, minute=0, second=0, microsecond=0)
            elif interval == "month":
                key = event.occurred_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                key = event.occurred_at

            interval_data[key] += 1

        # Convert to time series data points
        data_points = [
            TimeSeriesDataPoint(timestamp, count)
            for timestamp, count in sorted(interval_data.items())
        ]

        return data_points

    def generate_metric_time_series(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        interval: str = "day"
    ) -> List[TimeSeriesDataPoint]:
        """Generate time series for a calculated metric"""

        data_points = []
        current = start_time

        # Determine interval delta
        if interval == "hour":
            delta = timedelta(hours=1)
        elif interval == "day":
            delta = timedelta(days=1)
        elif interval == "week":
            delta = timedelta(weeks=1)
        elif interval == "month":
            delta = timedelta(days=30)
        else:
            delta = timedelta(days=1)

        while current <= end_time:
            # Calculate metric for this time point
            if metric_name == "fleet_availability":
                metric = self.calculate_fleet_availability(current - delta, current)
            elif metric_name == "mtbf":
                metric = self.calculate_mtbf(None, current - delta * 7, current)  # 7x window for MTBF
            elif metric_name == "mttr":
                metric = self.calculate_mttr(current - delta * 7, current)
            elif metric_name == "workorder_completion_rate":
                metric = self.calculate_workorder_completion_rate(current - delta, current)
            else:
                current += delta
                continue

            data_points.append(TimeSeriesDataPoint(current, metric.value))
            current += delta

        return data_points

    # =============================================================================
    # Aggregated Dashboard Metrics
    # =============================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get all key metrics for dashboard overview"""

        now = datetime.utcnow()

        return {
            "timestamp": now.isoformat(),
            "fleet": {
                "availability": self.calculate_fleet_availability().to_dict(),
                "mtbf": self.calculate_mtbf().to_dict(),
                "mttr": self.calculate_mttr().to_dict(),
                "total_vehicles": self.db.query(Vehicle).count()
            },
            "workorders": {
                "completion_rate": self.calculate_workorder_completion_rate().to_dict(),
                "active": self.db.query(WorkOrder).filter(WorkOrder.status == "in_progress").count(),
                "pending": self.db.query(WorkOrder).filter(WorkOrder.status == "pending").count(),
                "completed_today": self.db.query(WorkOrder).filter(
                    WorkOrder.status == "completed",
                    WorkOrder.updated_at >= now - timedelta(days=1)
                ).count()
            },
            "inventory": {
                "turnover": self.calculate_inventory_turnover().to_dict(),
                "stockout_rate": self.calculate_stockout_rate().to_dict(),
                "total_items": self.db.query(InventoryItem).count(),
                "low_stock_items": self.db.query(InventoryItem).filter(
                    InventoryItem.quantity < InventoryItem.reorder_point
                ).count()
            },
            "staff": {
                "total_active": self.db.query(StaffMember).filter(
                    StaffMember.status == "active"
                ).count()
            }
        }
