# Phase 3 API Reference

## Overview

Complete API reference for Phase 3 endpoints including Event Sourcing, CRDT Sync, Time-Travel, Machine Learning, and Analytics.

**Base URL**: `http://localhost:8000/api/v1`

**Authentication**: Bearer token (if enabled)

**Content-Type**: `application/json`

## Quick Reference

| Category | Endpoints | Purpose |
|----------|-----------|---------|
| Events | 5 endpoints | Event sourcing operations |
| Projections | 3 endpoints | CQRS projections |
| Sync (CRDT) | 7 endpoints | Offline synchronization |
| Time-Travel | 6 endpoints | Historical queries |
| Audit | 4 endpoints | Audit trails |
| Compliance | 3 endpoints | Compliance reports |
| ML | 8 endpoints | Machine learning |
| Analytics | 15 endpoints | Dashboards & metrics |

**Total**: 51 new Phase 3 endpoints

---

## Event Sourcing API

### Append Event

Create a new event in the event store.

```http
POST /events/
```

**Request Body**:
```json
{
  "aggregate_type": "Vehicle",
  "aggregate_id": "V001",
  "event_type": "VehicleCreated",
  "data": {
    "vehicle_number": "LOC-001",
    "vehicle_type": "Locomotive",
    "status": "active"
  },
  "metadata": {
    "user_id": "user123",
    "ip_address": "192.168.1.1"
  }
}
```

**Response**: `201 Created`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "aggregate_type": "Vehicle",
  "aggregate_id": "V001",
  "event_type": "VehicleCreated",
  "version": 1,
  "occurred_at": "2024-01-15T10:30:00Z",
  "data": {...},
  "metadata": {...}
}
```

### Get Events for Aggregate

Retrieve all events for a specific aggregate.

```http
GET /events/{aggregate_type}/{aggregate_id}
```

**Parameters**:
- `aggregate_type` (path): Type of aggregate (e.g., "Vehicle")
- `aggregate_id` (path): ID of aggregate
- `from_version` (query, optional): Start from version
- `to_version` (query, optional): End at version

**Example**:
```http
GET /events/Vehicle/V001?from_version=1&to_version=10
```

**Response**: `200 OK`
```json
[
  {
    "id": "...",
    "event_type": "VehicleCreated",
    "version": 1,
    "occurred_at": "2024-01-15T10:30:00Z",
    "data": {...}
  },
  {
    "id": "...",
    "event_type": "VehicleStatusChanged",
    "version": 2,
    "occurred_at": "2024-01-15T11:00:00Z",
    "data": {...}
  }
]
```

### Get Events by Type

Retrieve all events of a specific type.

```http
GET /events/type/{event_type}
```

**Parameters**:
- `event_type` (path): Type of event
- `limit` (query): Max number of events (default: 100)
- `offset` (query): Pagination offset

**Response**: `200 OK`

### Get Event Stream

Get recent events (event stream for real-time updates).

```http
GET /events/stream
```

**Parameters**:
- `since` (query): Timestamp to get events since
- `limit` (query): Max events

**Response**: `200 OK`

---

## Projections API

### Get Projection State

Get current state of a projection.

```http
GET /projections/{projection_name}/state
```

**Example**:
```http
GET /projections/vehicle_projection/state
```

**Response**: `200 OK`
```json
{
  "projection_name": "vehicle_projection",
  "last_processed_version": 1247,
  "last_updated": "2024-01-15T12:00:00Z",
  "status": "up_to_date"
}
```

### Rebuild Projection

Rebuild a projection from scratch.

```http
POST /projections/{projection_name}/rebuild
```

**Response**: `202 Accepted`
```json
{
  "status": "rebuilding",
  "message": "Projection rebuild started"
}
```

---

## CRDT Sync API

### Register Device

Register a new device for synchronization.

```http
POST /sync/devices/register
```

**Request Body**:
```json
{
  "device_id": "mobile-001",
  "device_type": "mobile",
  "device_name": "Field Tablet 1",
  "device_info": {
    "os": "Android 12",
    "app_version": "2.1.0"
  }
}
```

**Response**: `201 Created`
```json
{
  "device_id": "mobile-001",
  "status": "active",
  "registered_at": "2024-01-15T10:00:00Z"
}
```

### Push Changes

Push local changes to server (from device).

```http
POST /sync/push
```

**Request Body**:
```json
{
  "device_id": "mobile-001",
  "changes": [
    {
      "aggregate_type": "Vehicle",
      "aggregate_id": "V001",
      "crdt_type": "LWW-Register",
      "state": {
        "value": {"status": "maintenance"},
        "timestamp": "2024-01-15T11:30:00Z",
        "node_id": "mobile-001"
      },
      "vector_clock": {"mobile-001": 5}
    }
  ]
}
```

**Response**: `200 OK`
```json
{
  "accepted": 1,
  "conflicts": 0,
  "message": "Changes pushed successfully"
}
```

### Pull Changes

Pull server changes to device.

```http
GET /sync/pull/{device_id}
```

**Parameters**:
- `since_version` (query): Get changes since version

**Response**: `200 OK`
```json
{
  "changes": [
    {
      "aggregate_type": "WorkOrder",
      "aggregate_id": "WO001",
      "crdt_type": "LWW-Register",
      "state": {...},
      "vector_clock": {...}
    }
  ],
  "has_more": false
}
```

### Sync Status

Get sync status for a device.

```http
GET /sync/devices/{device_id}/status
```

**Response**: `200 OK`
```json
{
  "device_id": "mobile-001",
  "status": "active",
  "last_sync": "2024-01-15T12:30:00Z",
  "pending_changes": 0,
  "conflicts": 0
}
```

### List Devices

List all registered devices.

```http
GET /sync/devices/
```

**Response**: `200 OK`

### Resolve Conflict

Manually resolve a sync conflict.

```http
POST /sync/conflicts/{conflict_id}/resolve
```

**Request Body**:
```json
{
  "resolution_strategy": "server_wins",
  "resolved_state": {...}
}
```

**Response**: `200 OK`

---

## Time-Travel API

### Get State At Time

Get aggregate state at a specific point in time.

```http
GET /time-travel/state-at
```

**Parameters**:
- `aggregate_type` (query): Type of aggregate
- `aggregate_id` (query): ID of aggregate
- `timestamp` (query): ISO 8601 timestamp
- `version` (query): Alternative to timestamp

**Example**:
```http
GET /time-travel/state-at?aggregate_type=Vehicle&aggregate_id=V001&timestamp=2024-01-15T10:00:00Z
```

**Response**: `200 OK`
```json
{
  "aggregate_type": "Vehicle",
  "aggregate_id": "V001",
  "timestamp": "2024-01-15T10:00:00Z",
  "version": 5,
  "state": {
    "vehicle_number": "LOC-001",
    "status": "active",
    "location": "Depot A"
  }
}
```

### Get State History

Get history of state changes over time.

```http
GET /time-travel/history
```

**Parameters**:
- `aggregate_type`, `aggregate_id`
- `start_time`, `end_time`

**Response**: `200 OK`
```json
{
  "history": [
    {
      "timestamp": "2024-01-15T09:00:00Z",
      "version": 1,
      "state": {"status": "active"}
    },
    {
      "timestamp": "2024-01-15T11:00:00Z",
      "version": 3,
      "state": {"status": "maintenance"}
    }
  ]
}
```

### Compare States

Compare states between two time points.

```http
GET /time-travel/compare
```

**Parameters**:
- `aggregate_type`, `aggregate_id`
- `time1`, `time2`

**Response**: `200 OK`
```json
{
  "changes": [
    {
      "field": "status",
      "old_value": "active",
      "new_value": "maintenance",
      "changed_at": "2024-01-15T11:00:00Z"
    }
  ]
}
```

---

## Audit API

### Get Audit Trail

Get audit trail for an aggregate.

```http
GET /audit/trail
```

**Parameters**:
- `aggregate_type`, `aggregate_id`
- `start_time`, `end_time`

**Response**: `200 OK`
```json
{
  "entries": [
    {
      "event_type": "VehicleCreated",
      "occurred_at": "2024-01-15T09:00:00Z",
      "user_id": "user123",
      "ip_address": "192.168.1.1",
      "changes": {...}
    }
  ]
}
```

### Get Change History

Get detailed change history with diffs.

```http
GET /audit/changes
```

**Response**: `200 OK`

### Detect Anomalies

Detect anomalies in event patterns.

```http
GET /audit/anomalies
```

**Parameters**:
- `aggregate_type`, `aggregate_id`
- `start_time`, `end_time`

**Response**: `200 OK`
```json
{
  "anomalies": [
    {
      "type": "rapid_changes",
      "description": "10 changes within 1 second",
      "timestamp": "2024-01-15T11:30:00Z"
    }
  ]
}
```

---

## Compliance API

### Generate GDPR Report

Generate GDPR compliance report.

```http
GET /compliance/reports/gdpr
```

**Parameters**:
- `start_date`, `end_date`
- `scope`: "all", "user_data", "audit_only"

**Response**: `200 OK`
```json
{
  "report_type": "GDPR",
  "generated_at": "2024-01-15T12:00:00Z",
  "status": "pass",
  "checks": [
    {
      "check_name": "audit_trail_completeness",
      "passed": true,
      "details": "All events have complete audit trail"
    },
    {
      "check_name": "user_attribution",
      "passed": true,
      "details": "All changes attributed to users"
    }
  ],
  "recommendations": []
}
```

### Generate SOX Report

Generate SOX compliance report.

```http
GET /compliance/reports/sox
```

**Response**: `200 OK`

### Get User Data

Get all data for a specific user (GDPR right to access).

```http
GET /compliance/user-data/{user_id}
```

**Response**: `200 OK`

---

## Machine Learning API

### Train Model

Train a machine learning model.

```http
POST /ml/models/train
```

**Request Body**:
```json
{
  "model_name": "maintenance_predictor",
  "entity_type": "Vehicle",
  "entity_ids": ["V001", "V002", ...],
  "labels": [1, 0, 1, ...],
  "hyperparameters": {
    "n_estimators": 100,
    "max_depth": 10
  },
  "test_size": 0.2
}
```

**Response**: `202 Accepted`
```json
{
  "job_id": "train-job-001",
  "status": "training",
  "message": "Model training started"
}
```

### Get Training Job Status

Check training job status.

```http
GET /ml/training-jobs/{job_id}
```

**Response**: `200 OK`
```json
{
  "job_id": "train-job-001",
  "status": "completed",
  "progress": 100,
  "metrics": {
    "accuracy": 0.87,
    "precision": 0.85,
    "recall": 0.89
  },
  "model_id": "model-550e8400"
}
```

### List Models

List all trained models.

```http
GET /ml/models/
```

**Response**: `200 OK`
```json
[
  {
    "model_id": "model-001",
    "model_name": "maintenance_predictor",
    "version": "1.0.0",
    "created_at": "2024-01-15T10:00:00Z",
    "status": "active"
  }
]
```

### Predict Maintenance

Predict maintenance needs for a vehicle.

```http
GET /ml/predict/maintenance/{vehicle_id}
```

**Parameters**:
- `risk_level` (query): "low", "medium", "high", "critical"

**Response**: `200 OK`
```json
{
  "vehicle_id": "V001",
  "prediction": "needs_maintenance",
  "confidence": 0.87,
  "risk_score": 0.92,
  "risk_level": "high",
  "recommended_action": "Schedule maintenance within 7 days",
  "predicted_at": "2024-01-15T12:00:00Z"
}
```

### Predict Work Order Completion

Predict work order completion time.

```http
GET /ml/predict/workorder-completion/{workorder_id}
```

**Response**: `200 OK`
```json
{
  "workorder_id": "WO001",
  "predicted_completion_days": 3.5,
  "confidence": 0.82,
  "is_delayed": false,
  "predicted_at": "2024-01-15T12:00:00Z"
}
```

### Forecast Part Demand

Forecast inventory demand for a part.

```http
GET /ml/predict/demand/{part_id}
```

**Parameters**:
- `forecast_days` (query): Forecast horizon (default: 30)

**Response**: `200 OK`
```json
{
  "part_id": "PART-001",
  "forecast_days": 30,
  "forecasted_demand": 45.0,
  "confidence_interval": {
    "lower": 38.0,
    "upper": 52.0,
    "confidence": 0.95
  },
  "urgency": "medium",
  "recommended_order_quantity": 50,
  "forecasted_at": "2024-01-15T12:00:00Z"
}
```

---

## Analytics API

### Executive Dashboard

Get executive-level dashboard.

```http
GET /analytics/dashboard/executive
```

**Response**: `200 OK`
```json
{
  "title": "Executive Dashboard",
  "timestamp": "2024-01-15T12:00:00Z",
  "summary": {
    "fleet": {
      "availability": {"value": 95.5, "unit": "%", "trend": "up"},
      "mtbf": {"value": 720.0, "unit": "hours"},
      "mttr": {"value": 12.5, "unit": "hours"},
      "total_vehicles": 150
    },
    "workorders": {
      "completion_rate": {"value": 87.5, "unit": "%"},
      "active": 23,
      "pending": 15
    },
    "inventory": {
      "turnover": {"value": 1.2, "unit": "per month"},
      "stockout_rate": {"value": 3.5, "unit": "%"}
    }
  },
  "charts": [...],
  "insights": [...]
}
```

### Operations Dashboard

Get operations-level dashboard.

```http
GET /analytics/dashboard/operations
```

**Response**: `200 OK`

### Maintenance Dashboard

Get maintenance-focused dashboard.

```http
GET /analytics/dashboard/maintenance
```

**Response**: `200 OK`

### Inventory Dashboard

Get inventory-focused dashboard.

```http
GET /analytics/dashboard/inventory
```

**Response**: `200 OK`

### Metrics Summary

Get summary of all metrics.

```http
GET /analytics/metrics/summary
```

**Response**: `200 OK`

### Get KPIs

Get all key performance indicators.

```http
GET /analytics/kpis
```

**Response**: `200 OK`
```json
{
  "timestamp": "2024-01-15T12:00:00Z",
  "kpis": {
    "fleet_availability": {
      "value": 95.5,
      "unit": "%",
      "change_percentage": 2.3,
      "trend": "up"
    },
    "mtbf": {...},
    "mttr": {...},
    "workorder_completion_rate": {...},
    "inventory_turnover": {...},
    "stockout_rate": {...}
  }
}
```

### Get Specific Metric

Get a specific metric.

```http
GET /analytics/metrics/{metric_name}
```

**Metrics**:
- `fleet_availability`
- `mtbf`
- `mttr`
- `workorder_completion_rate`
- `inventory_turnover`
- `stockout_rate`

**Parameters**:
- `start_time`, `end_time` (query): Time range
- `vehicle_id` (query): For vehicle-specific metrics

**Response**: `200 OK`

### Get Metric Time Series

Get time series data for a metric.

```http
GET /analytics/timeseries/{metric_name}
```

**Parameters**:
- `start_time`, `end_time`
- `interval`: "hour", "day", "week", "month"

**Example**:
```http
GET /analytics/timeseries/fleet_availability?interval=day
```

**Response**: `200 OK`
```json
{
  "metric_name": "fleet_availability",
  "interval": "day",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "data": [
    {"timestamp": "2024-01-01T00:00:00Z", "value": 95.5},
    {"timestamp": "2024-01-02T00:00:00Z", "value": 96.2},
    ...
  ]
}
```

### Get Event Time Series

Get time series of event counts.

```http
GET /analytics/events/timeseries/{event_type}
```

**Parameters**:
- `start_time`, `end_time`
- `interval`: "hour", "day", "week", "month"

**Response**: `200 OK`

### Fleet Availability by Vehicle

Get availability breakdown by vehicle.

```http
GET /analytics/fleet/availability-by-vehicle
```

**Parameters**:
- `limit` (query): Max vehicles to return

**Response**: `200 OK`

### Work Order Performance

Get work order performance metrics.

```http
GET /analytics/workorders/performance
```

**Response**: `200 OK`
```json
{
  "period": {...},
  "status_distribution": {
    "pending": 15,
    "in_progress": 8,
    "completed": 342
  },
  "priority_distribution": {...},
  "average_completion_hours": 36.5,
  "overdue_count": 3
}
```

### Inventory Analysis

Get comprehensive inventory analysis.

```http
GET /analytics/inventory/analysis
```

**Response**: `200 OK`

### Health Check

Analytics service health check.

```http
GET /analytics/health
```

**Response**: `200 OK`
```json
{
  "status": "healthy",
  "service": "analytics",
  "version": "1.0.0"
}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid metric name: invalid_metric"
}
```

### 404 Not Found
```json
{
  "detail": "Vehicle V999 not found"
}
```

### 422 Validation Error
```json
{
  "detail": [
    {
      "loc": ["query", "interval"],
      "msg": "value must be one of: hour, day, week, month",
      "type": "value_error.const"
    }
  ]
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

| Endpoint Category | Rate Limit |
|------------------|------------|
| Events | 100 req/min |
| Sync | 500 req/min |
| Analytics | 60 req/min |
| ML Predictions | 30 req/min |
| Training | 5 req/hour |

---

## Pagination

List endpoints support pagination:

**Parameters**:
- `limit`: Items per page (default: 100, max: 1000)
- `offset`: Skip items

**Response includes**:
```json
{
  "items": [...],
  "total": 1247,
  "limit": 100,
  "offset": 0
}
```

---

## Testing with cURL

```bash
# Append event
curl -X POST http://localhost:8000/api/v1/events/ \
  -H "Content-Type: application/json" \
  -d '{"aggregate_type":"Vehicle","aggregate_id":"V001","event_type":"VehicleCreated","data":{"vehicle_number":"LOC-001"}}'

# Get KPIs
curl http://localhost:8000/api/v1/analytics/kpis

# Get time series
curl "http://localhost:8000/api/v1/analytics/timeseries/fleet_availability?interval=day"

# Predict maintenance
curl http://localhost:8000/api/v1/ml/predict/maintenance/V001
```

---

## SDK Examples

### Python
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get executive dashboard
response = requests.get(f"{BASE_URL}/analytics/dashboard/executive")
dashboard = response.json()
print(f"Fleet Availability: {dashboard['summary']['fleet']['availability']['value']}%")

# Predict maintenance
response = requests.get(f"{BASE_URL}/ml/predict/maintenance/V001")
prediction = response.json()
print(f"Maintenance needed: {prediction['prediction']}")
```

### JavaScript
```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Get KPIs
const response = await fetch(`${BASE_URL}/analytics/kpis`);
const data = await response.json();
console.log(`Fleet Availability: ${data.kpis.fleet_availability.value}%`);

// Get time series
const ts = await fetch(`${BASE_URL}/analytics/timeseries/fleet_availability?interval=day`);
const timeSeriesData = await ts.json();
```

---

## OpenAPI Schema

Full OpenAPI 3.0 schema available at:
```
GET /openapi.json
```

Interactive API documentation:
```
GET /docs        # Swagger UI
GET /redoc       # ReDoc
```

---

## Summary

Phase 3 adds 51 new API endpoints:
- ✅ 5 Event Sourcing endpoints
- ✅ 3 Projection endpoints
- ✅ 7 CRDT Sync endpoints
- ✅ 6 Time-Travel endpoints
- ✅ 4 Audit endpoints
- ✅ 3 Compliance endpoints
- ✅ 8 Machine Learning endpoints
- ✅ 15 Analytics endpoints

All endpoints are RESTful, JSON-based, and include comprehensive error handling.

Visit `/docs` for interactive API exploration.
