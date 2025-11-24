# Advanced Analytics Dashboard

## Overview

The Advanced Analytics Dashboard provides real-time insights, KPIs, and visualizations for RailFleet Manager. Built on top of the event sourcing infrastructure, it calculates metrics from historical event data and provides multiple dashboard views tailored to different roles.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Analytics Layer                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐    ┌──────────────────────┐      │
│  │ MetricsCalculator    │    │ DashboardService     │      │
│  │                      │    │                      │      │
│  │ - Fleet KPIs         │◄───┤ - Executive View     │      │
│  │ - Work Order KPIs    │    │ - Operations View    │      │
│  │ - Inventory KPIs     │    │ - Maintenance View   │      │
│  │ - Time Series        │    │ - Inventory View     │      │
│  └──────────────────────┘    └──────────────────────┘      │
│           ▲                           ▲                      │
│           │                           │                      │
│           └───────────┬───────────────┘                      │
│                       │                                       │
└───────────────────────┼───────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │    Event Sourcing Store       │
        │  (Historical Event Data)      │
        └───────────────────────────────┘
```

## Key Features

### 1. Real-Time KPI Calculation

Calculate key performance indicators from event sourcing data:

- **Fleet Availability**: Percentage of time vehicles are operational
- **MTBF (Mean Time Between Failures)**: Average time between vehicle failures
- **MTTR (Mean Time To Repair)**: Average time to complete repairs
- **Work Order Completion Rate**: Percentage of work orders completed on time
- **Inventory Turnover**: Rate of inventory consumption
- **Stockout Rate**: Percentage of time items are out of stock

### 2. Multiple Dashboard Views

**Executive Dashboard** (`/analytics/dashboard/executive`)
- High-level KPIs and trends
- 30-day overview
- Cost analysis
- Executive insights

**Operations Dashboard** (`/analytics/dashboard/operations`)
- Active work orders breakdown
- Vehicle status distribution
- Upcoming maintenance schedule
- 7-day operational focus

**Maintenance Dashboard** (`/analytics/dashboard/maintenance`)
- MTBF and MTTR trends
- Failure analysis
- Maintenance backlog
- Repair time distribution

**Inventory Dashboard** (`/analytics/dashboard/inventory`)
- Stock levels and alerts
- Low stock / overstock items
- ABC analysis
- Usage trends

### 3. Time Series Data

Generate time series data for charting:
- Configurable intervals (hour, day, week, month)
- Metric trends over time
- Event count trends
- Compatible with Chart.js and similar libraries

### 4. Actionable Insights

Automated insight generation:
- Low fleet availability warnings
- High work order backlog alerts
- Increasing repair time trends
- Low stock notifications

## API Endpoints

### Dashboard Endpoints

```http
GET /api/v1/analytics/dashboard/executive
GET /api/v1/analytics/dashboard/operations
GET /api/v1/analytics/dashboard/maintenance
GET /api/v1/analytics/dashboard/inventory
```

**Example Response** (Executive Dashboard):
```json
{
  "title": "Executive Dashboard",
  "timestamp": "2024-01-15T10:30:00",
  "summary": {
    "fleet": {
      "availability": {
        "value": 95.5,
        "unit": "%",
        "change_percentage": 2.3,
        "trend": "up"
      },
      "mtbf": { "value": 720.0, "unit": "hours" },
      "mttr": { "value": 12.5, "unit": "hours" },
      "total_vehicles": 150
    },
    "workorders": {
      "completion_rate": { "value": 87.5, "unit": "%" },
      "active": 23,
      "pending": 15,
      "completed_today": 8
    },
    "inventory": {
      "turnover": { "value": 1.2, "unit": "per month" },
      "stockout_rate": { "value": 3.5, "unit": "%" },
      "total_items": 450,
      "low_stock_items": 12
    }
  },
  "charts": [
    {
      "type": "line",
      "title": "Fleet Availability Trend (30 Days)",
      "labels": ["2024-01-01", "2024-01-02", ...],
      "datasets": [{
        "label": "Availability %",
        "data": [95.5, 96.2, 94.8, ...],
        "borderColor": "#4CAF50"
      }]
    }
  ],
  "insights": [
    {
      "title": "High Work Order Backlog",
      "message": "25 pending work orders. Consider allocating additional staff.",
      "severity": "warning",
      "action": "review_staffing"
    }
  ]
}
```

### Metrics Endpoints

```http
GET /api/v1/analytics/metrics/summary
GET /api/v1/analytics/metrics/{metric_name}?start_time=...&end_time=...
GET /api/v1/analytics/kpis
```

**Supported Metrics:**
- `fleet_availability`
- `mtbf`
- `mttr`
- `workorder_completion_rate`
- `inventory_turnover`
- `stockout_rate`

**Example Request:**
```http
GET /api/v1/analytics/metrics/fleet_availability?start_time=2024-01-01T00:00:00&end_time=2024-01-31T23:59:59
```

**Example Response:**
```json
{
  "name": "fleet_availability",
  "value": 95.5,
  "unit": "%",
  "timestamp": "2024-01-31T23:59:59",
  "change_percentage": 2.3,
  "trend": "up"
}
```

### Time Series Endpoints

```http
GET /api/v1/analytics/timeseries/{metric_name}?start_time=...&end_time=...&interval=day
GET /api/v1/analytics/events/timeseries/{event_type}?start_time=...&end_time=...&interval=day
```

**Intervals:** `hour`, `day`, `week`, `month`

**Example Request:**
```http
GET /api/v1/analytics/timeseries/fleet_availability?interval=day
```

**Example Response:**
```json
{
  "metric_name": "fleet_availability",
  "interval": "day",
  "period": {
    "start": "2024-01-01T00:00:00",
    "end": "2024-01-31T23:59:59"
  },
  "data": [
    { "timestamp": "2024-01-01T00:00:00", "value": 95.5 },
    { "timestamp": "2024-01-02T00:00:00", "value": 96.2 },
    ...
  ]
}
```

### Custom Analytics Endpoints

```http
GET /api/v1/analytics/fleet/availability-by-vehicle
GET /api/v1/analytics/workorders/performance
GET /api/v1/analytics/inventory/analysis
```

## Usage Examples

### Python Client

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"

# Get executive dashboard
response = requests.get(f"{BASE_URL}/analytics/dashboard/executive")
dashboard = response.json()

print(f"Fleet Availability: {dashboard['summary']['fleet']['availability']['value']}%")
print(f"Active Work Orders: {dashboard['summary']['workorders']['active']}")

# Get specific KPI
response = requests.get(f"{BASE_URL}/analytics/metrics/mtbf")
mtbf = response.json()
print(f"MTBF: {mtbf['value']} {mtbf['unit']}")

# Get time series data
params = {
    "start_time": (datetime.utcnow() - timedelta(days=30)).isoformat(),
    "end_time": datetime.utcnow().isoformat(),
    "interval": "day"
}
response = requests.get(
    f"{BASE_URL}/analytics/timeseries/fleet_availability",
    params=params
)
timeseries = response.json()
print(f"Data points: {len(timeseries['data'])}")
```

### JavaScript/React Example

```javascript
// Fetch executive dashboard
const response = await fetch('/api/v1/analytics/dashboard/executive');
const dashboard = await response.json();

// Display KPIs
console.log(`Fleet Availability: ${dashboard.summary.fleet.availability.value}%`);

// Render chart using Chart.js
import Chart from 'chart.js/auto';

const chartData = dashboard.charts[0]; // First chart
const ctx = document.getElementById('myChart').getContext('2d');

new Chart(ctx, {
  type: chartData.type,
  data: {
    labels: chartData.labels,
    datasets: chartData.datasets
  },
  options: chartData.options
});
```

### cURL Examples

```bash
# Get all KPIs
curl http://localhost:8000/api/v1/analytics/kpis

# Get operations dashboard
curl http://localhost:8000/api/v1/analytics/dashboard/operations

# Get time series with custom date range
curl "http://localhost:8000/api/v1/analytics/timeseries/fleet_availability?start_time=2024-01-01T00:00:00&end_time=2024-01-31T23:59:59&interval=week"

# Get work order performance
curl http://localhost:8000/api/v1/analytics/workorders/performance
```

## Running the Demo

A comprehensive demo script is included to showcase all analytics features:

```bash
python examples/analytics_dashboard_demo.py
```

The demo will:
1. Display executive dashboard data
2. Show individual KPI calculations
3. Demonstrate time series generation
4. Present operations, maintenance, and inventory dashboards
5. Explain chart data structures

## Performance Considerations

### Caching Strategy

For production deployments, consider implementing caching:

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=128)
def get_cached_dashboard(timestamp_hour: str):
    """Cache dashboard for 1 hour"""
    db = SessionLocal()
    service = DashboardService(db)
    return service.get_executive_dashboard()

# Use in endpoint
@router.get("/dashboard/executive")
def get_executive_dashboard():
    # Cache key: current hour
    cache_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
    return get_cached_dashboard(cache_key)
```

### Database Indexing

Ensure indexes exist on frequently queried fields:

```sql
-- Event table indexes
CREATE INDEX idx_events_type_occurred_at ON events(event_type, occurred_at);
CREATE INDEX idx_events_aggregate_type_id ON events(aggregate_type, aggregate_id);

-- Work order indexes
CREATE INDEX idx_workorders_status_created_at ON workorders(status, created_at);
CREATE INDEX idx_workorders_priority ON workorders(priority);

-- Inventory indexes
CREATE INDEX idx_inventory_quantity ON inventory_items(quantity);
```

### Asynchronous Calculation

For expensive calculations, use background tasks:

```python
from fastapi import BackgroundTasks

@router.get("/dashboard/executive")
async def get_executive_dashboard(background_tasks: BackgroundTasks):
    # Return cached data immediately
    cached = get_from_cache("executive_dashboard")

    # Refresh cache in background
    background_tasks.add_task(refresh_dashboard_cache)

    return cached
```

## Chart Visualization

The dashboard returns chart data compatible with popular JavaScript charting libraries:

### Chart.js Integration

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <canvas id="availabilityChart"></canvas>
    <script>
        fetch('/api/v1/analytics/dashboard/executive')
            .then(response => response.json())
            .then(data => {
                const chartData = data.charts[0]; // First chart
                new Chart(document.getElementById('availabilityChart'), {
                    type: chartData.type,
                    data: {
                        labels: chartData.labels,
                        datasets: chartData.datasets
                    },
                    options: chartData.options
                });
            });
    </script>
</body>
</html>
```

### Recharts (React) Integration

```jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

function AvailabilityChart() {
  const [data, setData] = useState([]);

  useEffect(() => {
    fetch('/api/v1/analytics/timeseries/fleet_availability?interval=day')
      .then(res => res.json())
      .then(result => {
        const chartData = result.data.map(point => ({
          date: new Date(point.timestamp).toLocaleDateString(),
          value: point.value
        }));
        setData(chartData);
      });
  }, []);

  return (
    <LineChart width={600} height={300} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
      <Line type="monotone" dataKey="value" stroke="#4CAF50" />
    </LineChart>
  );
}
```

## Extending the Analytics

### Adding New Metrics

1. Add calculation method to `MetricsCalculator`:

```python
def calculate_custom_metric(self, start_time, end_time) -> MetricValue:
    # Query event data
    events = self.db.query(Event).filter(...)

    # Calculate metric
    value = ...

    # Calculate trend
    prev_metric = self.calculate_custom_metric(prev_start, start_time)
    change_pct = ...
    trend = ...

    return MetricValue("custom_metric", value, "unit", end_time, change_pct, trend)
```

2. Add API endpoint in `analytics.py`:

```python
@router.get("/metrics/custom")
def get_custom_metric(db: Session = Depends(get_db)):
    calculator = MetricsCalculator(db)
    return calculator.calculate_custom_metric().to_dict()
```

### Adding New Dashboard Views

Create a new dashboard method in `DashboardService`:

```python
def get_custom_dashboard(self) -> Dict[str, Any]:
    # Calculate metrics
    metrics = {...}

    # Generate charts
    charts = [
        self._create_custom_chart(),
        ...
    ]

    # Generate insights
    insights = self._generate_custom_insights()

    return {
        "title": "Custom Dashboard",
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "charts": [c.to_dict() for c in charts],
        "insights": [i.to_dict() for i in insights]
    }
```

## Best Practices

1. **Metric Calculation Window**: Use appropriate time windows for each metric
   - Fleet availability: 30 days
   - MTBF/MTTR: 90 days (more stable)
   - Work order metrics: 30 days
   - Inventory: 90 days

2. **Time Series Resolution**: Choose appropriate intervals
   - Hour: For real-time monitoring (last 24 hours)
   - Day: For recent trends (last 30 days)
   - Week: For monthly/quarterly analysis
   - Month: For yearly comparisons

3. **Insight Severity Levels**:
   - `info`: Informational, no action required
   - `warning`: Attention needed, not urgent
   - `error`: Immediate action required
   - `success`: Positive outcome, celebrate!

4. **Caching**: Cache expensive calculations for 15-60 minutes

5. **Pagination**: For large datasets, implement pagination on time series endpoints

## Troubleshooting

### No Data in Dashboards

**Issue**: Dashboards show zero values or empty charts

**Solutions**:
- Ensure event sourcing is capturing events correctly
- Check that time ranges include actual event data
- Verify database has sufficient historical events
- Run `python examples/analytics_dashboard_demo.py` to test

### Slow Dashboard Loading

**Issue**: Dashboard API endpoints are slow

**Solutions**:
- Add database indexes on event tables
- Implement caching layer
- Reduce time range for expensive calculations
- Use background tasks for async calculation

### Incorrect Metric Values

**Issue**: Calculated metrics don't match expectations

**Solutions**:
- Verify event data quality and completeness
- Check metric calculation logic
- Ensure time zones are handled consistently (use UTC)
- Review trend calculation (compare with previous period)

## API Reference

For complete API documentation, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Navigate to the "Analytics" tag to see all available endpoints with detailed request/response schemas.

## Contributing

When adding new analytics features:

1. Add calculation logic to `MetricsCalculator`
2. Create visualization helpers in `DashboardService`
3. Add API endpoints in `analytics.py`
4. Update this documentation
5. Add examples to the demo script
6. Write unit tests for new metrics

## License

This module is part of RailFleet Manager and follows the same license.
