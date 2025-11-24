# Phase 3 Testing Documentation

## Overview

Comprehensive testing strategy for Phase 3 (Event Sourcing, CRDT, ML, Analytics) implementation. Includes integration tests, performance tests, and API contract tests.

## Test Architecture

```
tests/
├── integration/          # End-to-end integration tests
│   └── test_event_sourcing_flow.py
├── performance/          # Load and stress tests
│   └── test_load_performance.py
└── api/                  # API contract tests
    └── test_analytics_api.py

run_phase3_tests.py      # Test runner script
```

## Test Suites

### 1. Integration Tests (`tests/integration/`)

**Purpose**: Validate complete workflows from event creation to analytics dashboard.

#### Test Classes

**TestEventSourcingFlow**
- `test_vehicle_lifecycle_with_events`: Complete vehicle lifecycle
  - Create vehicle via event
  - Apply projection
  - Schedule maintenance
  - Update CRDT state
  - Sync to remote device
  - Calculate metrics
  - Generate dashboard

- `test_workorder_completion_flow`: Work order lifecycle
  - Create work order
  - Complete work order
  - Calculate completion rate
  - Generate operations dashboard

- `test_time_travel_query_integration`: Time-travel queries
  - Create events at different timestamps
  - Query state at specific time points
  - Verify state reconstruction

- `test_ml_prediction_integration`: ML pipeline
  - Create events with vehicle history
  - Extract features
  - Make prediction
  - Store prediction result

- `test_analytics_time_series_integration`: Time series generation
  - Create events over time
  - Generate time series data
  - Verify chart-ready format

- `test_compliance_report_integration`: Compliance reporting
  - Create events with attribution
  - Generate GDPR report
  - Verify audit completeness

**TestConcurrency**
- `test_concurrent_event_append`: Concurrent event appending with version control
- `test_crdt_conflict_resolution`: CRDT automatic conflict resolution

#### Running Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test
pytest tests/integration/test_event_sourcing_flow.py::TestEventSourcingFlow::test_vehicle_lifecycle_with_events -v

# Run with coverage
pytest tests/integration/ --cov=src --cov-report=html
```

### 2. Performance Tests (`tests/performance/`)

**Purpose**: Validate system performance under load and stress conditions.

#### Test Classes

**TestEventStorePerformance**
- `test_bulk_event_append`: Bulk event insertion (1000 events)
  - Target: >10 events/sec

- `test_event_query_performance`: Event query performance (50 queries)
  - Target: >20 queries/sec

- `test_event_replay_performance`: Event replay for projection rebuild (100 events)
  - Target: >100 events/sec

**TestAnalyticsPerformance**
- `test_metrics_calculation_performance`: All KPI calculations
  - Target: <5 seconds total

- `test_dashboard_generation_performance`: All dashboard generation
  - Target: <10 seconds total

- `test_time_series_generation_performance`: Time series data (30 days)
  - Target: <2 seconds

**TestConcurrentOperations**
- `test_concurrent_event_appends`: 10 threads, 50 events each
  - Target: >50 events/sec, >90% success rate

- `test_concurrent_metric_calculations`: 5 concurrent metric calculations
  - Target: <10 seconds total

**TestSyncPerformance**
- `test_sync_large_dataset`: Sync 1000 CRDT states
  - Target: <30 seconds

**TestStressScenarios**
- `test_stress_event_store`: Rapidly create 5000 events
  - Target: >90% success rate

- `test_stress_analytics_queries`: 100 rapid analytics queries
  - Target: >90% success rate

#### Running Performance Tests

```bash
# Run all performance tests
pytest tests/performance/ -v

# Run with performance report
pytest tests/performance/ -v --durations=10

# Run specific performance test
pytest tests/performance/test_load_performance.py::TestEventStorePerformance::test_bulk_event_append -v
```

#### Performance Benchmarks

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Event Append | >10/sec | >5/sec |
| Event Query | >20/sec | >10/sec |
| Event Replay | >100/sec | >50/sec |
| All KPIs | <5s | <10s |
| All Dashboards | <10s | <20s |
| Time Series (30d) | <2s | <5s |
| CRDT Sync (1000 states) | <30s | <60s |

### 3. API Contract Tests (`tests/api/`)

**Purpose**: Validate REST API endpoints conform to contracts.

#### Test Classes

**TestAnalyticsDashboardEndpoints**
- `test_executive_dashboard_endpoint`: Executive dashboard structure
- `test_operations_dashboard_endpoint`: Operations dashboard structure
- `test_maintenance_dashboard_endpoint`: Maintenance dashboard structure
- `test_inventory_dashboard_endpoint`: Inventory dashboard structure

**TestMetricsEndpoints**
- `test_metrics_summary_endpoint`: Metrics summary structure
- `test_kpis_endpoint`: All KPIs structure
- `test_specific_metric_endpoint`: Individual metric retrieval
- `test_invalid_metric_name`: Error handling
- `test_metric_with_time_range`: Time range parameters

**TestTimeSeriesEndpoints**
- `test_metric_timeseries_endpoint`: Metric time series structure
- `test_timeseries_intervals`: All interval types (hour, day, week, month)
- `test_timeseries_invalid_interval`: Invalid interval error handling
- `test_event_timeseries_endpoint`: Event time series structure
- `test_timeseries_custom_date_range`: Custom date range

**TestCustomAnalyticsEndpoints**
- `test_fleet_availability_by_vehicle`: Fleet availability breakdown
- `test_workorder_performance`: Work order performance metrics
- `test_inventory_analysis`: Inventory analysis

**TestHealthEndpoint**
- `test_analytics_health_endpoint`: Health check

**TestResponseFormats**
- `test_metric_response_format`: Metric format consistency
- `test_chart_data_format`: Chart data format consistency
- `test_timestamp_formats`: ISO 8601 timestamp format

**TestErrorHandling**
- `test_invalid_metric_name_error`: Invalid metric error response
- `test_invalid_query_params`: Invalid query parameter handling
- `test_malformed_date_params`: Malformed date handling

#### Running API Tests

```bash
# Run all API tests
pytest tests/api/ -v

# Run specific test class
pytest tests/api/test_analytics_api.py::TestMetricsEndpoints -v

# Run with API documentation check
pytest tests/api/ -v --tb=short
```

## Test Runner

### Usage

```bash
# Run all tests
python run_phase3_tests.py

# Run quick smoke tests
python run_phase3_tests.py --quick

# Check dependencies
python run_phase3_tests.py --check-deps

# Run specific suite
python run_phase3_tests.py --integration
python run_phase3_tests.py --performance
python run_phase3_tests.py --api
```

### Test Runner Output

The test runner provides:
- Real-time test execution output
- Pass/fail status for each suite
- Execution time per suite
- Overall summary with statistics
- Coverage report

Example output:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                      PHASE 3 TEST SUITE                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
  Running: Integration Tests - Event Sourcing Flow
================================================================================

test_vehicle_lifecycle_with_events ✓
test_workorder_completion_flow ✓
test_time_travel_query_integration ✓
test_ml_prediction_integration ✓
test_analytics_time_series_integration ✓
test_compliance_report_integration ✓
test_concurrent_event_append ✓
test_crdt_conflict_resolution ✓

✅ PASSED (12.45s)

...

╔══════════════════════════════════════════════════════════════════════════════╗
║                          TEST SUMMARY                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝

Test Suites:

  ✅ PASSED  Integration Tests - Event Sourcing Flow (12.45s)
  ✅ PASSED  Performance Tests - Load & Stress (45.67s)
  ✅ PASSED  API Contract Tests - Analytics (8.92s)

────────────────────────────────────────────────────────────────────────────────

Total Suites: 3
Passed: 3
Failed: 0
Duration: 67.04s

────────────────────────────────────────────────────────────────────────────────

🎉 ALL TESTS PASSED 🎉

Phase 3 implementation is verified and ready for production!
```

## Continuous Integration

### GitHub Actions Workflow

Create `.github/workflows/phase3-tests.yml`:

```yaml
name: Phase 3 Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: railfleet_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov

    - name: Run Phase 3 tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/railfleet_test
      run: |
        python run_phase3_tests.py

    - name: Generate coverage report
      run: |
        pytest tests/ --cov=src --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Test Data Setup

### Fixtures

Common fixtures in `conftest.py`:

```python
import pytest
from sqlalchemy.orm import Session
from src.database import SessionLocal, engine
from src.models import Base


@pytest.fixture(scope="function")
def db() -> Session:
    """Database session fixture"""
    # Create tables
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    # Drop tables
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_events(db: Session):
    """Create sample events for testing"""
    from src.services.event_store import EventStore

    event_store = EventStore(db)
    events = []

    for i in range(10):
        event = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id=f"V{i:03d}",
            event_type="VehicleCreated",
            data={"vehicle_number": f"LOC-{i:03d}"}
        )
        events.append(event)

    db.commit()
    return events
```

## Coverage Requirements

| Component | Target Coverage | Minimum Coverage |
|-----------|----------------|------------------|
| Event Store | >90% | >80% |
| Projections | >85% | >70% |
| CRDT Services | >90% | >80% |
| Sync Engine | >85% | >75% |
| Analytics | >80% | >70% |
| ML Services | >75% | >65% |
| API Endpoints | >95% | >85% |

### Measuring Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html

# Coverage by module
pytest tests/ --cov=src --cov-report=term-missing
```

## Troubleshooting

### Common Issues

**Database Connection Errors**
```
Error: could not connect to database
```
**Solution**: Ensure PostgreSQL is running and DATABASE_URL is correct

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Set DATABASE_URL
export DATABASE_URL="postgresql://user:password@localhost/railfleet_test"
```

**Import Errors**
```
ModuleNotFoundError: No module named 'src'
```
**Solution**: Ensure src is in PYTHONPATH

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Slow Tests**
```
Tests are running very slowly
```
**Solution**: Use in-memory database for tests

```python
# conftest.py
@pytest.fixture(scope="session")
def test_db_url():
    return "sqlite:///:memory:"
```

### Debug Mode

Run tests with verbose output:

```bash
# Maximum verbosity
pytest tests/ -vv --tb=long

# Show print statements
pytest tests/ -v -s

# Debug specific test
pytest tests/integration/test_event_sourcing_flow.py::TestEventSourcingFlow::test_vehicle_lifecycle_with_events -v -s --pdb
```

## Best Practices

1. **Isolation**: Each test should be independent and not rely on other tests
2. **Cleanup**: Always cleanup test data in fixtures
3. **Mocking**: Mock external dependencies (APIs, external services)
4. **Fast Tests**: Keep unit tests fast (<1s each)
5. **Descriptive Names**: Test names should describe what they test
6. **Arrange-Act-Assert**: Follow AAA pattern in test structure
7. **Edge Cases**: Test boundary conditions and error scenarios
8. **Performance**: Set realistic performance targets based on production requirements

## Maintenance

### Adding New Tests

When adding new Phase 3 features:

1. Add integration test in `tests/integration/`
2. Add performance test in `tests/performance/`
3. Add API test in `tests/api/`
4. Update this documentation
5. Run full test suite before committing

### Updating Performance Benchmarks

Review and update performance targets quarterly:

1. Run performance tests
2. Analyze trends
3. Adjust targets based on:
   - Hardware changes
   - Data volume growth
   - New features
   - Performance optimizations

## References

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [Coverage.py](https://coverage.readthedocs.io/)

## Summary

Phase 3 testing provides comprehensive validation of:
- ✅ Event Sourcing workflows
- ✅ CRDT synchronization
- ✅ Time-travel queries
- ✅ ML pipeline integration
- ✅ Analytics dashboards
- ✅ Performance benchmarks
- ✅ API contracts
- ✅ Concurrent operations
- ✅ Stress scenarios

Run `python run_phase3_tests.py` to verify all functionality.
