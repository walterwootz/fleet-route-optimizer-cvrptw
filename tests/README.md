
# RailFleet Manager - Test Suite

Comprehensive test suite for RailFleet Manager Phase 2 implementation.

## Test Structure

```
tests/
├── conftest.py                  # Pytest fixtures and configuration
├── e2e/                         # End-to-end integration tests
│   └── test_inventory_procurement_finance_flow.py
├── performance/                 # Performance benchmarks
│   └── test_performance.py
└── README.md                    # This file
```

## Setup

### 1. Install Test Dependencies

```bash
pip install -r requirements-test.txt
```

Test requirements:
- pytest >= 7.4.0
- pytest-asyncio >= 0.21.0
- pytest-cov >= 4.1.0
- httpx >= 0.24.1

### 2. Configure Test Database

Create a separate test database:

```bash
createdb railfleet_test
```

Set the test database URL:

```bash
export TEST_DATABASE_URL="postgresql://railfleet:railfleet@localhost:5432/railfleet_test"
```

### 3. Run Migrations

```bash
# Apply all migrations to test database
psql -U railfleet -d railfleet_test -f src/db/migrations/03_parts.sql
psql -U railfleet -d railfleet_test -f src/db/migrations/09_procurement.sql
psql -U railfleet -d railfleet_test -f src/db/migrations/10_finance.sql
```

## Running Tests

### Run All Tests

```bash
pytest tests/ -v
```

### Run E2E Tests Only

```bash
pytest tests/e2e/ -v -s
```

### Run Performance Tests

```bash
pytest tests/performance/ -v -s --tb=short
```

### Run with Coverage

```bash
pytest tests/ --cov=src --cov-report=html --cov-report=term
```

### Run Specific Test

```bash
pytest tests/e2e/test_inventory_procurement_finance_flow.py::TestInventoryProcurementFinanceFlow::test_complete_workflow -v -s
```

## Test Scenarios

### E2E Test: Complete Inventory-Procurement-Finance Flow

**File:** `tests/e2e/test_inventory_procurement_finance_flow.py`

**Scenario:**
1. ✅ Create Part
2. ✅ Create Stock Location
3. ✅ Create Supplier
4. ✅ Create Purchase Order (Status: DRAFT)
5. ✅ Approve PO (Status: APPROVED)
6. ✅ Order PO (Status: ORDERED)
7. ✅ Receive PO (Status: RECEIVED) → **Generates Stock Moves**
8. ✅ Verify Stock Moves Created
9. ✅ Create Budget
10. ✅ Create Invoice (Status: DRAFT)
11. ✅ Match Invoice against PO (Status: REVIEWED)
12. ✅ Approve Invoice (Status: APPROVED) → **Updates Budget**
13. ✅ Verify Budget Updated
14. ✅ Check Reports (Parts Usage, Cost Report)

**Expected Duration:** ~2-3 seconds

### Performance Tests

**File:** `tests/performance/test_performance.py`

**Benchmarks:**
- ✅ Bulk Part Creation (100 parts): < 30s
- ✅ Bulk Stock Moves (1,000 moves): < 120s
- ✅ Stock Overview Aggregation (10,000+ moves): < 5s
- ✅ Budget Overview (50+ cost centers): < 3s
- ✅ Parts Usage Report: < 5s
- ✅ Cost Report: < 3s
- ✅ Dashboard Summary: < 5s
- ✅ Concurrent Reads (50 requests): > 10 req/sec

## Test Markers

Use pytest markers to filter tests:

```bash
# Run only E2E tests
pytest -m e2e

# Run only performance tests
pytest -m performance

# Exclude slow tests
pytest -m "not slow"
```

## Continuous Integration

Add to CI/CD pipeline:

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: railfleet_test
          POSTGRES_USER: railfleet
          POSTGRES_PASSWORD: railfleet
        ports:
          - 5432:5432
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
          pip install -r requirements-test.txt

      - name: Run migrations
        run: |
          psql -U railfleet -d railfleet_test -f src/db/migrations/*.sql
        env:
          PGPASSWORD: railfleet

      - name: Run tests
        run: |
          pytest tests/ -v --cov=src --cov-report=xml
        env:
          TEST_DATABASE_URL: postgresql://railfleet:railfleet@localhost:5432/railfleet_test

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Debugging Tests

### Enable SQL Echo

Set environment variable:
```bash
export SQL_ECHO=true
pytest tests/ -v -s
```

### Use PDB

Add breakpoint in test:
```python
import pdb; pdb.set_trace()
```

Run with `-s` flag:
```bash
pytest tests/e2e/ -v -s
```

### View Test Output

Always use `-s` flag to see print statements:
```bash
pytest tests/ -v -s
```

## Test Data Cleanup

Tests use transactions that are rolled back after each test.
Manual cleanup not required for test database.

To reset test database completely:

```bash
dropdb railfleet_test
createdb railfleet_test
# Re-run migrations
```

## Performance Monitoring

### Generate Performance Report

```bash
pytest tests/performance/ -v -s > performance_report.txt
```

### Profile Tests

```bash
pip install pytest-profiling
pytest tests/ --profile
```

## Known Issues

1. **Auth Token Expiry**: Tests create new tokens for each run
2. **Parallel Execution**: Some tests may conflict with parallel execution
3. **Test Data**: Clean test database before running full suite

## Contributing

When adding new features:
1. Add E2E test for user workflows
2. Add performance test if feature involves bulk operations
3. Update this README with new test scenarios

## Questions?

See: docs/TESTING.md or contact the development team.
