"""
Advanced Analytics - Dashboard Service

Prepares comprehensive dashboard data with charts, KPIs, and insights.
Aggregates data across multiple dimensions for visualization.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from collections import defaultdict, Counter

from src.models.railfleet.event import Event
from src.models.railfleet.vehicle import Vehicle
from src.models.railfleet.workorder import WorkOrder
from src.models.railfleet.inventory import InventoryItem
from src.models.railfleet.staff import StaffMember
from src.services.analytics.metrics_calculator import MetricsCalculator, TimeSeriesDataPoint


class ChartData:
    """Represents data for a chart visualization"""

    def __init__(
        self,
        chart_type: str,  # 'line', 'bar', 'pie', 'area', 'scatter'
        title: str,
        labels: List[str],
        datasets: List[Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ):
        self.chart_type = chart_type
        self.title = title
        self.labels = labels
        self.datasets = datasets
        self.options = options or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.chart_type,
            "title": self.title,
            "labels": self.labels,
            "datasets": self.datasets,
            "options": self.options
        }


class InsightCard:
    """Represents an actionable insight card"""

    def __init__(
        self,
        title: str,
        message: str,
        severity: str,  # 'info', 'warning', 'error', 'success'
        action: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        self.title = title
        self.message = message
        self.severity = severity
        self.action = action
        self.data = data or {}

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "data": self.data
        }
        if self.action:
            result["action"] = self.action
        return result


class DashboardService:
    """
    Prepares comprehensive dashboard data for visualization.

    Provides:
    - Real-time KPI cards
    - Time series charts
    - Distribution charts
    - Actionable insights
    - Drill-down capabilities
    """

    def __init__(self, db: Session):
        self.db = db
        self.metrics_calculator = MetricsCalculator(db)

    # =============================================================================
    # Full Dashboard Views
    # =============================================================================

    def get_executive_dashboard(self) -> Dict[str, Any]:
        """
        Get executive-level dashboard with high-level KPIs and trends.

        Designed for management overview - focuses on business metrics.
        """
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)

        # Get key metrics
        summary = self.metrics_calculator.get_dashboard_summary()

        # Generate trend charts
        availability_chart = self._create_availability_trend_chart(last_30_days, now)
        workorder_chart = self._create_workorder_status_chart()
        cost_chart = self._create_cost_trend_chart(last_30_days, now)

        # Generate insights
        insights = self._generate_executive_insights()

        return {
            "title": "Executive Dashboard",
            "timestamp": now.isoformat(),
            "summary": summary,
            "charts": [
                availability_chart.to_dict(),
                workorder_chart.to_dict(),
                cost_chart.to_dict()
            ],
            "insights": [insight.to_dict() for insight in insights],
            "period": {
                "start": last_30_days.isoformat(),
                "end": now.isoformat()
            }
        }

    def get_operations_dashboard(self) -> Dict[str, Any]:
        """
        Get operations-level dashboard with detailed operational metrics.

        Designed for operations managers - focuses on day-to-day operations.
        """
        now = datetime.utcnow()
        last_7_days = now - timedelta(days=7)

        # Get operational metrics
        active_workorders = self._get_active_workorders_breakdown()
        vehicle_status = self._get_vehicle_status_breakdown()
        maintenance_schedule = self._get_upcoming_maintenance()

        # Generate charts
        workorder_timeline = self._create_workorder_timeline_chart(last_7_days, now)
        vehicle_utilization = self._create_vehicle_utilization_chart()
        parts_usage = self._create_parts_usage_chart(last_7_days, now)

        # Generate insights
        insights = self._generate_operational_insights()

        return {
            "title": "Operations Dashboard",
            "timestamp": now.isoformat(),
            "operations": {
                "active_workorders": active_workorders,
                "vehicle_status": vehicle_status,
                "upcoming_maintenance": maintenance_schedule
            },
            "charts": [
                workorder_timeline.to_dict(),
                vehicle_utilization.to_dict(),
                parts_usage.to_dict()
            ],
            "insights": [insight.to_dict() for insight in insights]
        }

    def get_maintenance_dashboard(self) -> Dict[str, Any]:
        """
        Get maintenance-focused dashboard.

        Designed for maintenance teams - focuses on maintenance metrics and schedules.
        """
        now = datetime.utcnow()
        last_90_days = now - timedelta(days=90)

        # Get maintenance metrics
        mtbf = self.metrics_calculator.calculate_mtbf()
        mttr = self.metrics_calculator.calculate_mttr()

        # Generate charts
        failure_analysis = self._create_failure_analysis_chart(last_90_days, now)
        maintenance_backlog = self._create_maintenance_backlog_chart()
        repair_time_dist = self._create_repair_time_distribution_chart()

        # Get maintenance schedule
        upcoming = self._get_upcoming_maintenance()

        # Generate insights
        insights = self._generate_maintenance_insights()

        return {
            "title": "Maintenance Dashboard",
            "timestamp": now.isoformat(),
            "metrics": {
                "mtbf": mtbf.to_dict(),
                "mttr": mttr.to_dict()
            },
            "upcoming_maintenance": upcoming,
            "charts": [
                failure_analysis.to_dict(),
                maintenance_backlog.to_dict(),
                repair_time_dist.to_dict()
            ],
            "insights": [insight.to_dict() for insight in insights]
        }

    def get_inventory_dashboard(self) -> Dict[str, Any]:
        """
        Get inventory-focused dashboard.

        Designed for inventory managers - focuses on stock levels and usage.
        """
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)

        # Get inventory metrics
        turnover = self.metrics_calculator.calculate_inventory_turnover()
        stockout_rate = self.metrics_calculator.calculate_stockout_rate()

        # Generate charts
        stock_levels = self._create_stock_levels_chart()
        usage_trend = self._create_inventory_usage_chart(last_30_days, now)
        abc_analysis = self._create_abc_analysis_chart()

        # Get alerts
        low_stock_items = self._get_low_stock_items()
        overstock_items = self._get_overstock_items()

        # Generate insights
        insights = self._generate_inventory_insights()

        return {
            "title": "Inventory Dashboard",
            "timestamp": now.isoformat(),
            "metrics": {
                "turnover": turnover.to_dict(),
                "stockout_rate": stockout_rate.to_dict()
            },
            "alerts": {
                "low_stock": low_stock_items,
                "overstock": overstock_items
            },
            "charts": [
                stock_levels.to_dict(),
                usage_trend.to_dict(),
                abc_analysis.to_dict()
            ],
            "insights": [insight.to_dict() for insight in insights]
        }

    # =============================================================================
    # Chart Generators
    # =============================================================================

    def _create_availability_trend_chart(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ChartData:
        """Create fleet availability trend line chart"""

        data_points = self.metrics_calculator.generate_metric_time_series(
            "fleet_availability",
            start_time,
            end_time,
            interval="day"
        )

        labels = [dp.timestamp.strftime("%Y-%m-%d") for dp in data_points]
        values = [dp.value for dp in data_points]

        return ChartData(
            chart_type="line",
            title="Fleet Availability Trend (30 Days)",
            labels=labels,
            datasets=[{
                "label": "Availability %",
                "data": values,
                "borderColor": "#4CAF50",
                "backgroundColor": "rgba(76, 175, 80, 0.1)",
                "tension": 0.4
            }],
            options={
                "scales": {
                    "y": {
                        "min": 0,
                        "max": 100,
                        "title": {"display": True, "text": "Availability (%)"}
                    }
                }
            }
        )

    def _create_workorder_status_chart(self) -> ChartData:
        """Create work order status distribution pie chart"""

        statuses = ["pending", "in_progress", "completed", "cancelled"]
        counts = []

        for status in statuses:
            count = self.db.query(WorkOrder).filter(WorkOrder.status == status).count()
            counts.append(count)

        return ChartData(
            chart_type="pie",
            title="Work Order Status Distribution",
            labels=["Pending", "In Progress", "Completed", "Cancelled"],
            datasets=[{
                "data": counts,
                "backgroundColor": [
                    "#FFC107",  # Pending - Yellow
                    "#2196F3",  # In Progress - Blue
                    "#4CAF50",  # Completed - Green
                    "#F44336"   # Cancelled - Red
                ]
            }]
        )

    def _create_cost_trend_chart(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ChartData:
        """Create maintenance cost trend chart"""

        # Group maintenance events by day
        events = self.db.query(Event).filter(
            Event.event_type.in_(["WorkOrderCreated", "MaintenanceCompleted"]),
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        ).order_by(Event.occurred_at).all()

        # Aggregate by day
        daily_costs = defaultdict(float)
        for event in events:
            day = event.occurred_at.date()
            # Estimate cost from event data
            cost = event.data.get("estimated_cost", 500)  # Default $500
            daily_costs[day] += cost

        labels = [str(day) for day in sorted(daily_costs.keys())]
        values = [daily_costs[day] for day in sorted(daily_costs.keys())]

        return ChartData(
            chart_type="bar",
            title="Daily Maintenance Costs",
            labels=labels,
            datasets=[{
                "label": "Cost ($)",
                "data": values,
                "backgroundColor": "#2196F3"
            }],
            options={
                "scales": {
                    "y": {
                        "title": {"display": True, "text": "Cost ($)"}
                    }
                }
            }
        )

    def _create_workorder_timeline_chart(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ChartData:
        """Create work order creation/completion timeline"""

        created_series = self.metrics_calculator.generate_event_time_series(
            "WorkOrderCreated",
            start_time,
            end_time,
            interval="day"
        )

        completed_series = self.metrics_calculator.generate_event_time_series(
            "WorkOrderCompleted",
            start_time,
            end_time,
            interval="day"
        )

        # Merge timelines
        all_dates = sorted(set(
            [dp.timestamp.strftime("%Y-%m-%d") for dp in created_series] +
            [dp.timestamp.strftime("%Y-%m-%d") for dp in completed_series]
        ))

        created_map = {dp.timestamp.strftime("%Y-%m-%d"): dp.value for dp in created_series}
        completed_map = {dp.timestamp.strftime("%Y-%m-%d"): dp.value for dp in completed_series}

        created_values = [created_map.get(date, 0) for date in all_dates]
        completed_values = [completed_map.get(date, 0) for date in all_dates]

        return ChartData(
            chart_type="line",
            title="Work Order Timeline (7 Days)",
            labels=all_dates,
            datasets=[
                {
                    "label": "Created",
                    "data": created_values,
                    "borderColor": "#FFC107",
                    "backgroundColor": "rgba(255, 193, 7, 0.1)"
                },
                {
                    "label": "Completed",
                    "data": completed_values,
                    "borderColor": "#4CAF50",
                    "backgroundColor": "rgba(76, 175, 80, 0.1)"
                }
            ]
        )

    def _create_vehicle_utilization_chart(self) -> ChartData:
        """Create vehicle utilization bar chart"""

        # Get vehicles with work order counts
        vehicles = self.db.query(Vehicle).limit(10).all()

        labels = [v.vehicle_number for v in vehicles]
        utilization = []

        for vehicle in vehicles:
            # Count recent work orders as proxy for utilization
            wo_count = self.db.query(WorkOrder).filter(
                WorkOrder.vehicle_id == vehicle.id,
                WorkOrder.created_at >= datetime.utcnow() - timedelta(days=30)
            ).count()
            # Normalize to percentage (assume 10 WO = 100% utilization)
            utilization.append(min(100, wo_count * 10))

        return ChartData(
            chart_type="bar",
            title="Vehicle Utilization (Top 10)",
            labels=labels,
            datasets=[{
                "label": "Utilization %",
                "data": utilization,
                "backgroundColor": "#2196F3"
            }],
            options={
                "scales": {
                    "y": {
                        "min": 0,
                        "max": 100,
                        "title": {"display": True, "text": "Utilization (%)"}
                    }
                }
            }
        )

    def _create_parts_usage_chart(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ChartData:
        """Create parts usage chart"""

        # Get inventory usage events
        events = self.db.query(Event).filter(
            Event.event_type == "InventoryItemUsed",
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        ).all()

        # Count by part
        part_usage = Counter()
        for event in events:
            part_number = event.data.get("part_number", "Unknown")
            quantity = event.data.get("quantity", 1)
            part_usage[part_number] += quantity

        # Top 10 most used parts
        top_parts = part_usage.most_common(10)
        labels = [part for part, _ in top_parts]
        values = [count for _, count in top_parts]

        return ChartData(
            chart_type="bar",
            title="Top 10 Parts Usage",
            labels=labels,
            datasets=[{
                "label": "Units Used",
                "data": values,
                "backgroundColor": "#FF9800"
            }]
        )

    def _create_failure_analysis_chart(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ChartData:
        """Create failure analysis chart by vehicle"""

        # Get breakdown events
        events = self.db.query(Event).filter(
            Event.event_type == "VehicleBreakdownReported",
            Event.occurred_at >= start_time,
            Event.occurred_at <= end_time
        ).all()

        # Count by vehicle
        vehicle_failures = Counter(event.aggregate_id for event in events)

        # Top 10 vehicles with most failures
        top_vehicles = vehicle_failures.most_common(10)
        labels = [vid for vid, _ in top_vehicles]
        values = [count for _, count in top_vehicles]

        return ChartData(
            chart_type="bar",
            title="Failure Analysis - Top 10 Vehicles (90 Days)",
            labels=labels,
            datasets=[{
                "label": "Failures",
                "data": values,
                "backgroundColor": "#F44336"
            }]
        )

    def _create_maintenance_backlog_chart(self) -> ChartData:
        """Create maintenance backlog chart by priority"""

        priorities = ["low", "medium", "high", "critical"]
        counts = []

        for priority in priorities:
            count = self.db.query(WorkOrder).filter(
                WorkOrder.priority == priority,
                WorkOrder.status.in_(["pending", "in_progress"])
            ).count()
            counts.append(count)

        return ChartData(
            chart_type="bar",
            title="Maintenance Backlog by Priority",
            labels=["Low", "Medium", "High", "Critical"],
            datasets=[{
                "data": counts,
                "backgroundColor": ["#4CAF50", "#FFC107", "#FF9800", "#F44336"]
            }]
        )

    def _create_repair_time_distribution_chart(self) -> ChartData:
        """Create repair time distribution histogram"""

        # Get completed work orders from last 90 days
        completed = self.db.query(WorkOrder).filter(
            WorkOrder.status == "completed",
            WorkOrder.updated_at >= datetime.utcnow() - timedelta(days=90)
        ).all()

        # Calculate repair times in hours
        repair_times = []
        for wo in completed:
            if wo.created_at and wo.updated_at:
                hours = (wo.updated_at - wo.created_at).total_seconds() / 3600
                repair_times.append(hours)

        # Create buckets: 0-4h, 4-8h, 8-24h, 24-48h, 48+h
        buckets = [0, 0, 0, 0, 0]
        for time in repair_times:
            if time < 4:
                buckets[0] += 1
            elif time < 8:
                buckets[1] += 1
            elif time < 24:
                buckets[2] += 1
            elif time < 48:
                buckets[3] += 1
            else:
                buckets[4] += 1

        return ChartData(
            chart_type="bar",
            title="Repair Time Distribution",
            labels=["0-4h", "4-8h", "8-24h", "24-48h", "48+h"],
            datasets=[{
                "label": "Work Orders",
                "data": buckets,
                "backgroundColor": "#9C27B0"
            }]
        )

    def _create_stock_levels_chart(self) -> ChartData:
        """Create current stock levels chart"""

        items = self.db.query(InventoryItem).order_by(InventoryItem.quantity.desc()).limit(15).all()

        labels = [item.part_number for item in items]
        quantities = [item.quantity for item in items]
        reorder_points = [item.reorder_point for item in items]

        return ChartData(
            chart_type="bar",
            title="Current Stock Levels (Top 15 Items)",
            labels=labels,
            datasets=[
                {
                    "label": "Current Quantity",
                    "data": quantities,
                    "backgroundColor": "#2196F3"
                },
                {
                    "label": "Reorder Point",
                    "data": reorder_points,
                    "backgroundColor": "#FFC107",
                    "type": "line"
                }
            ]
        )

    def _create_inventory_usage_chart(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> ChartData:
        """Create inventory usage trend chart"""

        usage_series = self.metrics_calculator.generate_event_time_series(
            "InventoryItemUsed",
            start_time,
            end_time,
            interval="day"
        )

        labels = [dp.timestamp.strftime("%Y-%m-%d") for dp in usage_series]
        values = [dp.value for dp in usage_series]

        return ChartData(
            chart_type="area",
            title="Daily Parts Usage Trend",
            labels=labels,
            datasets=[{
                "label": "Parts Used",
                "data": values,
                "backgroundColor": "rgba(33, 150, 243, 0.3)",
                "borderColor": "#2196F3"
            }]
        )

    def _create_abc_analysis_chart(self) -> ChartData:
        """Create ABC analysis chart (Pareto principle)"""

        # Get all items sorted by usage value
        items = self.db.query(InventoryItem).all()

        # Calculate usage value (quantity * estimated cost)
        item_values = [(item.part_number, item.quantity * 50) for item in items]  # $50 avg cost
        item_values.sort(key=lambda x: x[1], reverse=True)

        # Take top 20
        top_20 = item_values[:20]
        labels = [item[0] for item in top_20]
        values = [item[1] for item in top_20]

        return ChartData(
            chart_type="bar",
            title="ABC Analysis - Inventory Value (Top 20)",
            labels=labels,
            datasets=[{
                "label": "Value ($)",
                "data": values,
                "backgroundColor": "#00BCD4"
            }]
        )

    # =============================================================================
    # Helper Methods
    # =============================================================================

    def _get_active_workorders_breakdown(self) -> Dict[str, int]:
        """Get breakdown of active work orders"""
        return {
            "total": self.db.query(WorkOrder).filter(
                WorkOrder.status.in_(["pending", "in_progress"])
            ).count(),
            "high_priority": self.db.query(WorkOrder).filter(
                WorkOrder.status.in_(["pending", "in_progress"]),
                WorkOrder.priority.in_(["high", "critical"])
            ).count(),
            "overdue": self.db.query(WorkOrder).filter(
                WorkOrder.status.in_(["pending", "in_progress"]),
                WorkOrder.created_at < datetime.utcnow() - timedelta(days=7)
            ).count()
        }

    def _get_vehicle_status_breakdown(self) -> Dict[str, int]:
        """Get breakdown of vehicle statuses"""
        statuses = ["active", "maintenance", "out_of_service"]
        breakdown = {}
        for status in statuses:
            breakdown[status] = self.db.query(Vehicle).filter(Vehicle.status == status).count()
        return breakdown

    def _get_upcoming_maintenance(self) -> List[Dict[str, Any]]:
        """Get upcoming maintenance schedule"""
        # Get maintenance events for next 7 days
        now = datetime.utcnow()
        next_week = now + timedelta(days=7)

        events = self.db.query(Event).filter(
            Event.event_type == "VehicleMaintenanceScheduled",
            Event.occurred_at >= now,
            Event.occurred_at <= next_week
        ).order_by(Event.occurred_at).limit(10).all()

        return [
            {
                "vehicle_id": event.aggregate_id,
                "scheduled_at": event.occurred_at.isoformat(),
                "type": event.data.get("maintenance_type", "routine"),
                "priority": event.data.get("priority", "medium")
            }
            for event in events
        ]

    def _get_low_stock_items(self) -> List[Dict[str, Any]]:
        """Get items below reorder point"""
        items = self.db.query(InventoryItem).filter(
            InventoryItem.quantity < InventoryItem.reorder_point
        ).limit(10).all()

        return [
            {
                "part_number": item.part_number,
                "quantity": item.quantity,
                "reorder_point": item.reorder_point,
                "deficit": item.reorder_point - item.quantity
            }
            for item in items
        ]

    def _get_overstock_items(self) -> List[Dict[str, Any]]:
        """Get potentially overstocked items"""
        # Items with quantity > 3x reorder point
        items = self.db.query(InventoryItem).filter(
            InventoryItem.quantity > InventoryItem.reorder_point * 3
        ).limit(10).all()

        return [
            {
                "part_number": item.part_number,
                "quantity": item.quantity,
                "reorder_point": item.reorder_point,
                "excess": item.quantity - (item.reorder_point * 2)
            }
            for item in items
        ]

    # =============================================================================
    # Insight Generators
    # =============================================================================

    def _generate_executive_insights(self) -> List[InsightCard]:
        """Generate executive-level insights"""
        insights = []

        # Check fleet availability
        availability = self.metrics_calculator.calculate_fleet_availability()
        if availability.value < 85:
            insights.append(InsightCard(
                title="Low Fleet Availability",
                message=f"Fleet availability is at {availability.value}%, below the 85% target. "
                        f"Consider increasing maintenance resources.",
                severity="warning",
                action="review_maintenance_schedule"
            ))

        # Check work order backlog
        backlog = self.db.query(WorkOrder).filter(
            WorkOrder.status == "pending"
        ).count()
        if backlog > 20:
            insights.append(InsightCard(
                title="High Work Order Backlog",
                message=f"{backlog} pending work orders. Consider allocating additional staff.",
                severity="warning",
                action="review_staffing"
            ))

        return insights

    def _generate_operational_insights(self) -> List[InsightCard]:
        """Generate operations-level insights"""
        insights = []

        # Check overdue work orders
        overdue = self.db.query(WorkOrder).filter(
            WorkOrder.status.in_(["pending", "in_progress"]),
            WorkOrder.created_at < datetime.utcnow() - timedelta(days=7)
        ).count()

        if overdue > 0:
            insights.append(InsightCard(
                title="Overdue Work Orders",
                message=f"{overdue} work orders are overdue (>7 days). Review and prioritize.",
                severity="error",
                action="review_overdue_workorders"
            ))

        return insights

    def _generate_maintenance_insights(self) -> List[InsightCard]:
        """Generate maintenance-level insights"""
        insights = []

        # Check MTTR trend
        mttr = self.metrics_calculator.calculate_mttr()
        if mttr.trend == "up" and mttr.change_percentage > 10:
            insights.append(InsightCard(
                title="Increasing Repair Times",
                message=f"MTTR has increased by {mttr.change_percentage}%. "
                        f"Investigate repair process bottlenecks.",
                severity="warning",
                action="analyze_repair_process"
            ))

        return insights

    def _generate_inventory_insights(self) -> List[InsightCard]:
        """Generate inventory-level insights"""
        insights = []

        # Check low stock items
        low_stock_count = self.db.query(InventoryItem).filter(
            InventoryItem.quantity < InventoryItem.reorder_point
        ).count()

        if low_stock_count > 0:
            insights.append(InsightCard(
                title="Low Stock Alert",
                message=f"{low_stock_count} items are below reorder point. Place procurement orders.",
                severity="warning",
                action="create_procurement_order",
                data={"low_stock_count": low_stock_count}
            ))

        return insights
