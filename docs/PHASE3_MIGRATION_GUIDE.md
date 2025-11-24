# Phase 3 Migration Guide

## Overview

This guide walks you through migrating to Phase 3 of RailFleet Manager, which introduces:
- Event Sourcing & CQRS architecture
- CRDT-based offline synchronization
- Time-travel queries and audit trails
- Machine learning predictive models
- Advanced analytics dashboards

## Prerequisites

- Existing RailFleet Manager Phase 2 installation
- PostgreSQL 12+ database
- Python 3.11+
- Backup of existing database

## Migration Strategy

Phase 3 is **additive** and maintains backward compatibility with Phase 2 APIs. You can migrate gradually without disrupting existing functionality.

### Migration Phases

1. **Preparation** (1-2 hours)
   - Backup database
   - Review changes
   - Update dependencies

2. **Database Migration** (30 minutes)
   - Run Alembic migrations
   - Verify schema changes

3. **Event Sourcing Bootstrap** (1-2 hours)
   - Generate historical events from existing data
   - Verify event store

4. **Feature Rollout** (Gradual)
   - Enable event sourcing for new operations
   - Enable CRDT sync for mobile clients
   - Deploy analytics dashboards
   - Train ML models

5. **Validation** (1 hour)
   - Run test suite
   - Verify all features
   - Performance testing

**Total estimated time**: 5-8 hours

## Step-by-Step Migration

### Step 1: Backup Database

```bash
# Create backup
pg_dump -h localhost -U postgres railfleet > railfleet_backup_$(date +%Y%m%d).sql

# Verify backup
ls -lh railfleet_backup_*.sql
```

### Step 2: Update Dependencies

```bash
# Pull latest code
git pull origin main

# Update Python dependencies
pip install -r requirements.txt

# Verify installations
python -c "import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')"
python -c "import sklearn; print(f'scikit-learn: {sklearn.__version__}')"
```

### Step 3: Run Database Migrations

Phase 3 adds 3 new migrations:

```bash
# View pending migrations
alembic current
alembic history

# Run migrations
alembic upgrade head

# Verify migrations
alembic current
```

**New tables created**:
- `events` - Event store
- `projections_metadata` - Projection tracking
- `crdt_states` - CRDT state storage
- `sync_devices` - Device registration
- `sync_sessions` - Sync session tracking
- `ml_models` - ML model metadata
- `ml_predictions` - Prediction results

### Step 4: Bootstrap Event Store

Generate historical events from existing Phase 2 data:

```bash
# Run bootstrap script
python scripts/bootstrap_event_store.py

# Expected output:
# ✓ Processing 150 vehicles...
# ✓ Processing 342 work orders...
# ✓ Processing 89 inventory items...
# ✓ Generated 1,247 events
# ✓ Bootstrap complete
```

**What this does**:
- Creates `VehicleCreated` events for all vehicles
- Creates `WorkOrderCreated` events for all work orders
- Creates `InventoryItemCreated` events for inventory
- Maintains chronological order based on `created_at` timestamps

### Step 5: Verify Event Store

```bash
# Run verification script
python scripts/verify_event_store.py

# Check event counts
psql -h localhost -U postgres railfleet -c "SELECT COUNT(*) FROM events;"
psql -h localhost -U postgres railfleet -c "SELECT event_type, COUNT(*) FROM events GROUP BY event_type;"
```

Expected output:
```
event_type              | count
------------------------+-------
VehicleCreated          |   150
WorkOrderCreated        |   342
InventoryItemCreated    |    89
```

### Step 6: Enable Event Sourcing (Gradual)

Event sourcing can be enabled gradually per module:

**6.1 Enable for Vehicles**

```python
# In src/api/v1/endpoints/vehicles.py

from src.services.event_store import EventStore

@router.post("/vehicles/")
def create_vehicle(vehicle: VehicleCreate, db: Session = Depends(get_db)):
    # Create vehicle (existing code)
    new_vehicle = Vehicle(**vehicle.dict())
    db.add(new_vehicle)
    db.commit()

    # NEW: Append event
    event_store = EventStore(db)
    event_store.append_event(
        aggregate_type="Vehicle",
        aggregate_id=new_vehicle.id,
        event_type="VehicleCreated",
        data=vehicle.dict(),
        metadata={"user_id": "system"}  # Add actual user from auth
    )

    return new_vehicle
```

**6.2 Enable for Work Orders**

Similar pattern for work orders, inventory, etc.

**6.3 Test Event Sourcing**

```bash
# Create test vehicle via API
curl -X POST http://localhost:8000/api/v1/vehicles/ \
  -H "Content-Type: application/json" \
  -d '{"vehicle_number": "TEST-001", "vehicle_type": "Locomotive"}'

# Verify event created
psql -h localhost -U postgres railfleet -c "SELECT * FROM events WHERE aggregate_id = 'TEST-001';"
```

### Step 7: Deploy CRDT Sync (Optional)

CRDT sync is for mobile/offline clients:

**7.1 Register Devices**

```bash
# Register a mobile device
curl -X POST http://localhost:8000/api/v1/sync/devices/register \
  -H "Content-Type: application/json" \
  -d '{"device_id": "mobile-001", "device_type": "mobile", "device_name": "Field Tablet 1"}'
```

**7.2 Test Sync**

```bash
# Push changes from device
curl -X POST http://localhost:8000/api/v1/sync/push \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "mobile-001",
    "changes": [{
      "aggregate_type": "Vehicle",
      "aggregate_id": "V001",
      "crdt_type": "LWW-Register",
      "state": {...}
    }]
  }'

# Pull changes to device
curl http://localhost:8000/api/v1/sync/pull/mobile-001
```

### Step 8: Deploy Analytics Dashboards

Analytics dashboards are immediately available after migration:

**8.1 Access Dashboards**

```bash
# Executive dashboard
curl http://localhost:8000/api/v1/analytics/dashboard/executive

# Operations dashboard
curl http://localhost:8000/api/v1/analytics/dashboard/operations
```

**8.2 Integrate with Frontend**

```javascript
// React example
import { useEffect, useState } from 'react';
import Chart from 'chart.js/auto';

function ExecutiveDashboard() {
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    fetch('/api/v1/analytics/dashboard/executive')
      .then(res => res.json())
      .then(data => setDashboard(data));
  }, []);

  if (!dashboard) return <div>Loading...</div>;

  return (
    <div>
      <h1>{dashboard.title}</h1>
      <KPICards kpis={dashboard.summary} />
      <Charts charts={dashboard.charts} />
      <Insights insights={dashboard.insights} />
    </div>
  );
}
```

### Step 9: Train ML Models

**9.1 Prepare Training Data**

```bash
# Extract features for all vehicles
python scripts/extract_ml_features.py --entity-type Vehicle
```

**9.2 Train Maintenance Predictor**

```bash
# Train model
python examples/train_maintenance_model.py

# Expected output:
# ✓ Extracted features for 150 vehicles
# ✓ Training on 120 samples, testing on 30
# ✓ Model accuracy: 0.87
# ✓ Model saved to ./models/maintenance_predictor_v1.pkl
```

**9.3 Deploy Model**

```bash
# Upload model via API
curl -X POST http://localhost:8000/api/v1/ml/models/upload \
  -F "file=@models/maintenance_predictor_v1.pkl" \
  -F "model_name=maintenance_predictor" \
  -F "version=1.0.0"
```

**9.4 Make Predictions**

```bash
# Predict maintenance for vehicle
curl http://localhost:8000/api/v1/ml/predict/maintenance/V001
```

### Step 10: Run Tests

```bash
# Run Phase 3 test suite
python run_phase3_tests.py

# Expected output:
# ✅ PASSED  Integration Tests (12s)
# ✅ PASSED  Performance Tests (45s)
# ✅ PASSED  API Tests (8s)
# 🎉 ALL TESTS PASSED
```

### Step 11: Performance Validation

```bash
# Run performance benchmarks
pytest tests/performance/ -v

# Verify targets:
# ✓ Event append: >10/sec
# ✓ Event query: >20/sec
# ✓ Analytics KPIs: <5s
# ✓ Dashboards: <10s
```

## Rollback Plan

If issues arise during migration:

### Rollback Database

```bash
# Stop application
systemctl stop railfleet

# Restore backup
psql -h localhost -U postgres railfleet < railfleet_backup_YYYYMMDD.sql

# Downgrade migrations
alembic downgrade -1  # Go back one migration
# or
alembic downgrade <revision>  # Go back to specific revision

# Restart application
systemctl start railfleet
```

### Partial Rollback

If only specific features have issues:

**Disable Event Sourcing**
```python
# Comment out event_store.append_event() calls
# Existing functionality continues to work
```

**Disable CRDT Sync**
```python
# Set feature flag
ENABLE_CRDT_SYNC = False
```

**Disable Analytics**
```python
# Remove analytics router
# app.include_router(analytics.router)
```

## Configuration Changes

### Environment Variables

Add to `.env` or environment:

```bash
# Event Sourcing
EVENT_STORE_ENABLED=true
EVENT_RETENTION_DAYS=365

# CRDT Sync
SYNC_ENABLED=true
SYNC_BATCH_SIZE=100

# ML Models
ML_MODELS_PATH=./models
ML_ENABLE_PREDICTIONS=true

# Analytics
ANALYTICS_CACHE_TTL=900  # 15 minutes
```

### Database Connection Pool

Phase 3 may require larger connection pool:

```python
# src/database.py

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,          # Increased from 10
    max_overflow=40,        # Increased from 20
    pool_pre_ping=True
)
```

## Breaking Changes

**None**. Phase 3 is fully backward compatible.

All existing Phase 2 APIs continue to work unchanged. Phase 3 adds new capabilities without modifying existing functionality.

## New API Endpoints

Phase 3 adds ~50 new endpoints:

### Event Sourcing
- `POST /events/` - Append event
- `GET /events/{aggregate_type}/{aggregate_id}` - Get events
- `GET /projections/{projection_name}` - Get projection state

### CRDT Sync
- `POST /sync/devices/register` - Register device
- `POST /sync/push` - Push changes
- `GET /sync/pull/{device_id}` - Pull changes

### Time-Travel & Audit
- `GET /time-travel/state-at` - Get state at time
- `GET /audit/trail` - Get audit trail
- `GET /compliance/reports/gdpr` - GDPR compliance report

### Machine Learning
- `POST /ml/models/train` - Train model
- `GET /ml/predict/maintenance/{vehicle_id}` - Maintenance prediction
- `GET /ml/predict/demand/{part_id}` - Demand forecast

### Analytics
- `GET /analytics/dashboard/executive` - Executive dashboard
- `GET /analytics/dashboard/operations` - Operations dashboard
- `GET /analytics/metrics/summary` - Metrics summary
- `GET /analytics/kpis` - All KPIs
- `GET /analytics/timeseries/{metric}` - Time series data

See [API Documentation](API_REFERENCE.md) for complete endpoint list.

## Monitoring & Observability

### Key Metrics to Monitor

**Event Store**
```sql
-- Event append rate
SELECT COUNT(*) FROM events WHERE occurred_at > NOW() - INTERVAL '1 hour';

-- Event backlog
SELECT COUNT(*) FROM events WHERE processed = false;
```

**Sync Performance**
```sql
-- Active sync sessions
SELECT COUNT(*) FROM sync_sessions WHERE status = 'active';

-- Sync success rate
SELECT
  status,
  COUNT(*) * 100.0 / SUM(COUNT(*)) OVER() as percentage
FROM sync_sessions
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY status;
```

**Analytics Performance**
```sql
-- Dashboard query times (add application metrics)
-- KPI calculation times
-- Time series generation times
```

### Logging

Enable detailed logging:

```python
# src/config.py

LOG_LEVEL = "INFO"  # or "DEBUG" for verbose

# Event sourcing logs
logger.info(f"Event appended: {event.event_type} for {event.aggregate_id}")

# Sync logs
logger.info(f"Sync completed: {result.merged_count} merged, {result.conflict_count} conflicts")
```

## Troubleshooting

### Event Store Issues

**Problem**: Events not appearing in event store

**Solution**:
```python
# Check if event_store.append_event() is called
# Verify database connection
# Check logs for exceptions
```

**Problem**: Event version conflicts

**Solution**:
```python
# Events must be appended in order
# Use optimistic locking (version check)
# Retry on conflict
```

### CRDT Sync Issues

**Problem**: Sync conflicts not resolving

**Solution**:
```python
# Verify vector clocks are updating
# Check CRDT merge logic
# Ensure timestamps are synchronized (NTP)
```

### Analytics Performance Issues

**Problem**: Dashboard slow to load

**Solution**:
```python
# Enable caching (15-minute TTL)
# Add database indexes
# Use background tasks for expensive calculations
```

### ML Prediction Issues

**Problem**: Predictions failing

**Solution**:
```python
# Verify model is trained and uploaded
# Check feature extraction succeeds
# Ensure model file exists and is valid
```

## Post-Migration Tasks

1. **Monitor Performance**
   - Watch database CPU/memory
   - Monitor API response times
   - Check error rates

2. **Train Team**
   - Introduce new analytics dashboards
   - Explain event sourcing benefits
   - Document CRDT sync for mobile team

3. **Optimize**
   - Add database indexes based on query patterns
   - Fine-tune cache TTLs
   - Adjust connection pool sizes

4. **Document**
   - Update internal documentation
   - Create user guides
   - Record common issues and solutions

## Support

For issues during migration:

1. Check logs: `tail -f logs/railfleet.log`
2. Review [Troubleshooting Guide](TROUBLESHOOTING.md)
3. Run diagnostics: `python scripts/diagnose.py`
4. Contact support: support@railfleet.example.com

## Summary

Phase 3 migration checklist:

- [ ] Backup database
- [ ] Update dependencies
- [ ] Run database migrations (alembic upgrade head)
- [ ] Bootstrap event store
- [ ] Verify event store
- [ ] Enable event sourcing gradually
- [ ] Deploy CRDT sync (if using mobile)
- [ ] Deploy analytics dashboards
- [ ] Train ML models
- [ ] Run test suite
- [ ] Validate performance
- [ ] Monitor in production
- [ ] Train team
- [ ] Update documentation

**Estimated migration time**: 5-8 hours

**Rollback time**: <30 minutes

Phase 3 is production-ready and battle-tested. Follow this guide for smooth migration.
