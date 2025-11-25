"""
Analytics Dashboard Demo

Demonstrates how to use the Advanced Analytics Dashboard API endpoints.

This script shows:
1. Fetching executive-level dashboard data
2. Getting specific KPIs (availability, MTBF, MTTR)
3. Retrieving time series data for charts
4. Accessing operations and maintenance dashboards
5. Getting inventory analysis

Usage:
    python examples/analytics_dashboard_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from src.database import SessionLocal
from src.services.analytics.metrics_calculator import MetricsCalculator
from src.services.analytics.dashboard_service import DashboardService


def print_section(title: str):
    """Print a section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def demo_executive_dashboard(db: Session):
    """Demo: Executive Dashboard"""
    print_section("Executive Dashboard")

    dashboard_service = DashboardService(db)
    dashboard = dashboard_service.get_executive_dashboard()

    print(f"📊 Dashboard generated at: {dashboard['timestamp']}")
    print(f"📅 Period: {dashboard['period']['start']} to {dashboard['period']['end']}\n")

    # Print summary metrics
    print("🔑 Key Metrics:")
    summary = dashboard['summary']

    print(f"\n  Fleet:")
    print(f"    • Availability: {summary['fleet']['availability']['value']}% "
          f"({summary['fleet']['availability']['trend']} {summary['fleet']['availability']['change_percentage']}%)")
    print(f"    • MTBF: {summary['fleet']['mtbf']['value']} {summary['fleet']['mtbf']['unit']}")
    print(f"    • MTTR: {summary['fleet']['mttr']['value']} {summary['fleet']['mttr']['unit']}")
    print(f"    • Total Vehicles: {summary['fleet']['total_vehicles']}")

    print(f"\n  Work Orders:")
    print(f"    • Completion Rate: {summary['workorders']['completion_rate']['value']}%")
    print(f"    • Active: {summary['workorders']['active']}")
    print(f"    • Pending: {summary['workorders']['pending']}")
    print(f"    • Completed Today: {summary['workorders']['completed_today']}")

    print(f"\n  Inventory:")
    print(f"    • Turnover: {summary['inventory']['turnover']['value']} {summary['inventory']['turnover']['unit']}")
    print(f"    • Stockout Rate: {summary['inventory']['stockout_rate']['value']}%")
    print(f"    • Total Items: {summary['inventory']['total_items']}")
    print(f"    • Low Stock Items: {summary['inventory']['low_stock_items']}")

    # Print charts info
    print(f"\n📈 Available Charts: {len(dashboard['charts'])}")
    for i, chart in enumerate(dashboard['charts'], 1):
        print(f"    {i}. {chart['title']} ({chart['type']})")

    # Print insights
    print(f"\n💡 Insights: {len(dashboard['insights'])}")
    for insight in dashboard['insights']:
        severity_icon = {
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅'
        }
        icon = severity_icon.get(insight['severity'], '•')
        print(f"    {icon} {insight['title']}")
        print(f"       {insight['message']}")


def demo_kpi_metrics(db: Session):
    """Demo: Individual KPI Metrics"""
    print_section("Individual KPI Metrics")

    calculator = MetricsCalculator(db)

    # Fleet Availability
    availability = calculator.calculate_fleet_availability()
    print(f"🚂 Fleet Availability:")
    print(f"    Value: {availability.value}% {availability.unit}")
    print(f"    Change: {availability.change_percentage}% ({availability.trend})")
    print(f"    Timestamp: {availability.timestamp}")

    # MTBF
    mtbf = calculator.calculate_mtbf()
    print(f"\n⏱️  Mean Time Between Failures (MTBF):")
    print(f"    Value: {mtbf.value} {mtbf.unit}")
    print(f"    Change: {mtbf.change_percentage}% ({mtbf.trend})")

    # MTTR
    mttr = calculator.calculate_mttr()
    print(f"\n🔧 Mean Time To Repair (MTTR):")
    print(f"    Value: {mttr.value} {mttr.unit}")
    print(f"    Change: {mttr.change_percentage}% ({mttr.trend})")

    # Work Order Completion Rate
    completion = calculator.calculate_workorder_completion_rate()
    print(f"\n✅ Work Order Completion Rate:")
    print(f"    Value: {completion.value}%")
    print(f"    Change: {completion.change_percentage}% ({completion.trend})")

    # Inventory Turnover
    turnover = calculator.calculate_inventory_turnover()
    print(f"\n📦 Inventory Turnover:")
    print(f"    Value: {turnover.value} {turnover.unit}")
    print(f"    Change: {turnover.change_percentage}% ({turnover.trend})")


def demo_time_series(db: Session):
    """Demo: Time Series Data"""
    print_section("Time Series Data for Charts")

    calculator = MetricsCalculator(db)
    now = datetime.utcnow()
    start = now - timedelta(days=7)

    # Fleet availability over time
    availability_series = calculator.generate_metric_time_series(
        "fleet_availability",
        start,
        now,
        interval="day"
    )

    print(f"📈 Fleet Availability Time Series (Last 7 Days):")
    print(f"    Data points: {len(availability_series)}")
    if availability_series:
        print(f"    Range: {availability_series[0].value}% to {availability_series[-1].value}%")
        print(f"\n    Sample data:")
        for dp in availability_series[:3]:
            print(f"      {dp.timestamp.strftime('%Y-%m-%d')}: {dp.value}%")

    # Event time series
    event_series = calculator.generate_event_time_series(
        "WorkOrderCreated",
        start,
        now,
        interval="day"
    )

    print(f"\n📋 Work Order Creation Time Series (Last 7 Days):")
    print(f"    Data points: {len(event_series)}")
    total_events = sum(dp.value for dp in event_series)
    print(f"    Total work orders created: {total_events}")
    if event_series:
        print(f"\n    Sample data:")
        for dp in event_series[:3]:
            print(f"      {dp.timestamp.strftime('%Y-%m-%d')}: {int(dp.value)} work orders")


def demo_operations_dashboard(db: Session):
    """Demo: Operations Dashboard"""
    print_section("Operations Dashboard")

    dashboard_service = DashboardService(db)
    dashboard = dashboard_service.get_operations_dashboard()

    print(f"🏭 Operations Dashboard generated at: {dashboard['timestamp']}\n")

    # Active work orders
    print("📋 Active Work Orders:")
    wo = dashboard['operations']['active_workorders']
    print(f"    Total: {wo['total']}")
    print(f"    High Priority: {wo['high_priority']}")
    print(f"    Overdue: {wo['overdue']}")

    # Vehicle status
    print("\n🚂 Vehicle Status:")
    vs = dashboard['operations']['vehicle_status']
    for status, count in vs.items():
        print(f"    {status}: {count}")

    # Upcoming maintenance
    print("\n🔧 Upcoming Maintenance:")
    maintenance = dashboard['operations']['upcoming_maintenance']
    print(f"    Scheduled items: {len(maintenance)}")
    for item in maintenance[:3]:
        print(f"      • Vehicle {item['vehicle_id']}: {item['type']} "
              f"({item['priority']} priority) at {item['scheduled_at']}")

    # Charts
    print(f"\n📊 Available Charts: {len(dashboard['charts'])}")
    for chart in dashboard['charts']:
        print(f"    • {chart['title']}")

    # Insights
    print(f"\n💡 Operational Insights: {len(dashboard['insights'])}")
    for insight in dashboard['insights']:
        print(f"    ⚠️  {insight['title']}: {insight['message']}")


def demo_maintenance_dashboard(db: Session):
    """Demo: Maintenance Dashboard"""
    print_section("Maintenance Dashboard")

    dashboard_service = DashboardService(db)
    dashboard = dashboard_service.get_maintenance_dashboard()

    print(f"🔧 Maintenance Dashboard generated at: {dashboard['timestamp']}\n")

    # Metrics
    print("📊 Maintenance Metrics:")
    mtbf = dashboard['metrics']['mtbf']
    mttr = dashboard['metrics']['mttr']
    print(f"    MTBF: {mtbf['value']} {mtbf['unit']} ({mtbf['trend']} {mtbf['change_percentage']}%)")
    print(f"    MTTR: {mttr['value']} {mttr['unit']} ({mttr['trend']} {mttr['change_percentage']}%)")

    # Upcoming maintenance
    print(f"\n📅 Upcoming Maintenance: {len(dashboard['upcoming_maintenance'])} items")
    for item in dashboard['upcoming_maintenance'][:3]:
        print(f"    • {item['vehicle_id']}: {item['type']} at {item['scheduled_at']}")

    # Charts
    print(f"\n📈 Charts:")
    for chart in dashboard['charts']:
        print(f"    • {chart['title']} ({chart['type']})")

    # Insights
    print(f"\n💡 Maintenance Insights:")
    for insight in dashboard['insights']:
        print(f"    {insight['severity'].upper()}: {insight['title']}")
        print(f"        {insight['message']}")


def demo_inventory_dashboard(db: Session):
    """Demo: Inventory Dashboard"""
    print_section("Inventory Dashboard")

    dashboard_service = DashboardService(db)
    dashboard = dashboard_service.get_inventory_dashboard()

    print(f"📦 Inventory Dashboard generated at: {dashboard['timestamp']}\n")

    # Metrics
    print("📊 Inventory Metrics:")
    turnover = dashboard['metrics']['turnover']
    stockout = dashboard['metrics']['stockout_rate']
    print(f"    Turnover: {turnover['value']} {turnover['unit']} ({turnover['trend']})")
    print(f"    Stockout Rate: {stockout['value']}% ({stockout['trend']})")

    # Alerts
    print(f"\n⚠️  Inventory Alerts:")
    alerts = dashboard['alerts']
    print(f"    Low Stock Items: {len(alerts['low_stock'])}")
    for item in alerts['low_stock'][:3]:
        print(f"      • {item['part_number']}: {item['quantity']} units "
              f"(reorder: {item['reorder_point']}, deficit: {item['deficit']})")

    print(f"\n    Overstock Items: {len(alerts['overstock'])}")
    for item in alerts['overstock'][:3]:
        print(f"      • {item['part_number']}: {item['quantity']} units "
              f"(reorder: {item['reorder_point']}, excess: {item['excess']})")

    # Charts
    print(f"\n📈 Charts:")
    for chart in dashboard['charts']:
        print(f"    • {chart['title']} ({chart['type']})")

    # Insights
    if dashboard['insights']:
        print(f"\n💡 Inventory Insights:")
        for insight in dashboard['insights']:
            print(f"    {insight['severity'].upper()}: {insight['title']}")
            print(f"        {insight['message']}")


def demo_chart_data_structure():
    """Demo: Understanding Chart Data Structure"""
    print_section("Chart Data Structure")

    print("""
📊 Chart Data Structure:

Charts returned by the API have the following structure:

{
    "type": "line",              # Chart type: line, bar, pie, area, scatter
    "title": "Fleet Availability Trend",
    "labels": ["2024-01-01", "2024-01-02", ...],  # X-axis labels
    "datasets": [
        {
            "label": "Availability %",
            "data": [95.5, 96.2, 94.8, ...],     # Y-axis values
            "borderColor": "#4CAF50",
            "backgroundColor": "rgba(76, 175, 80, 0.1)",
            "tension": 0.4                        # Line smoothness
        }
    ],
    "options": {                   # Chart.js options
        "scales": {
            "y": {
                "min": 0,
                "max": 100,
                "title": {"display": true, "text": "Availability (%)"}
            }
        }
    }
}

This structure is compatible with Chart.js, a popular JavaScript charting library.
You can directly pass this data to Chart.js or similar visualization libraries.
    """)


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "RAILFLEET ANALYTICS DASHBOARD DEMO" + " " * 24 + "║")
    print("╚" + "═" * 78 + "╝")

    db = SessionLocal()

    try:
        # Run demos
        demo_executive_dashboard(db)
        demo_kpi_metrics(db)
        demo_time_series(db)
        demo_operations_dashboard(db)
        demo_maintenance_dashboard(db)
        demo_inventory_dashboard(db)
        demo_chart_data_structure()

        # Summary
        print_section("API Endpoints Summary")
        print("""
🌐 Available Analytics API Endpoints:

Executive Level:
    GET /api/v1/analytics/dashboard/executive

Operations Level:
    GET /api/v1/analytics/dashboard/operations

Maintenance Focus:
    GET /api/v1/analytics/dashboard/maintenance

Inventory Focus:
    GET /api/v1/analytics/dashboard/inventory

Metrics:
    GET /api/v1/analytics/metrics/summary
    GET /api/v1/analytics/metrics/{metric_name}?start_time=...&end_time=...
    GET /api/v1/analytics/kpis

Time Series:
    GET /api/v1/analytics/timeseries/{metric_name}?interval=day
    GET /api/v1/analytics/events/timeseries/{event_type}?interval=day

Custom Analytics:
    GET /api/v1/analytics/fleet/availability-by-vehicle
    GET /api/v1/analytics/workorders/performance
    GET /api/v1/analytics/inventory/analysis

Health Check:
    GET /api/v1/analytics/health
        """)

        print("\n✅ Demo completed successfully!\n")

    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()


if __name__ == "__main__":
    main()
