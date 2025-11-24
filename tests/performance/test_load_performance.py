"""
Performance Tests - Load & Stress Testing

Tests system performance under load with concurrent requests,
large datasets, and stress scenarios.
"""

import pytest
import time
import concurrent.futures
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session

from src.models.railfleet.event import Event
from src.services.event_store import EventStore
from src.services.analytics.metrics_calculator import MetricsCalculator
from src.services.analytics.dashboard_service import DashboardService
from src.services.sync_engine import SyncEngine


class PerformanceMetrics:
    """Track performance metrics"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.operations = 0
        self.errors = 0

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    @property
    def duration(self) -> float:
        """Duration in seconds"""
        if not self.end_time or not self.start_time:
            return 0
        return self.end_time - self.start_time

    @property
    def ops_per_second(self) -> float:
        """Operations per second"""
        if self.duration == 0:
            return 0
        return self.operations / self.duration

    def to_dict(self):
        return {
            "operations": self.operations,
            "errors": self.errors,
            "duration_seconds": round(self.duration, 2),
            "ops_per_second": round(self.ops_per_second, 2)
        }


class TestEventStorePerformance:
    """Test event store performance"""

    def test_bulk_event_append(self, db: Session):
        """Test bulk event insertion performance"""
        metrics = PerformanceMetrics()
        event_store = EventStore(db)

        metrics.start()

        # Append 1000 events
        for i in range(1000):
            try:
                event_store.append_event(
                    aggregate_type="Vehicle",
                    aggregate_id=f"V_PERF_{i % 100}",  # 100 vehicles
                    event_type="VehicleStatusChanged",
                    data={"status": "active", "iteration": i},
                    metadata={"test": "performance"}
                )
                metrics.operations += 1
            except Exception as e:
                metrics.errors += 1
                print(f"Error appending event {i}: {e}")

        db.commit()
        metrics.stop()

        print(f"\n📊 Bulk Event Append Performance:")
        print(f"   Operations: {metrics.operations}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Throughput: {metrics.ops_per_second:.2f} events/sec")

        # Performance assertions
        assert metrics.ops_per_second > 10, "Event append should handle >10 ops/sec"
        assert metrics.errors < 10, "Error rate should be <1%"

    def test_event_query_performance(self, db: Session):
        """Test event query performance with large dataset"""
        event_store = EventStore(db)

        # Setup: Create 1000 events
        for i in range(1000):
            event_store.append_event(
                aggregate_type="Vehicle",
                aggregate_id=f"V_QUERY_{i % 50}",
                event_type="VehicleCreated",
                data={"index": i}
            )
        db.commit()

        metrics = PerformanceMetrics()
        metrics.start()

        # Query all events for aggregate
        for vehicle_id in range(50):
            events = event_store.get_events("Vehicle", f"V_QUERY_{vehicle_id}")
            assert len(events) > 0
            metrics.operations += 1

        metrics.stop()

        print(f"\n📊 Event Query Performance:")
        print(f"   Queries: {metrics.operations}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Throughput: {metrics.ops_per_second:.2f} queries/sec")

        assert metrics.ops_per_second > 20, "Query should handle >20 ops/sec"

    def test_event_replay_performance(self, db: Session):
        """Test event replay performance (projection rebuild)"""
        event_store = EventStore(db)

        # Setup: Create event history
        aggregate_id = "V_REPLAY_TEST"
        for i in range(100):
            event_store.append_event(
                aggregate_type="Vehicle",
                aggregate_id=aggregate_id,
                event_type="VehicleStatusChanged",
                data={"status": f"status_{i}", "version": i}
            )
        db.commit()

        metrics = PerformanceMetrics()
        metrics.start()

        # Replay all events
        events = event_store.get_events("Vehicle", aggregate_id)

        # Simulate projection application
        state = {}
        for event in events:
            state.update(event.data)
            metrics.operations += 1

        metrics.stop()

        print(f"\n📊 Event Replay Performance:")
        print(f"   Events replayed: {metrics.operations}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Throughput: {metrics.ops_per_second:.2f} events/sec")

        assert metrics.ops_per_second > 100, "Replay should handle >100 events/sec"


class TestAnalyticsPerformance:
    """Test analytics performance"""

    def test_metrics_calculation_performance(self, db: Session):
        """Test KPI calculation performance"""
        # Setup: Create test data
        event_store = EventStore(db)
        for i in range(100):
            event_store.append_event(
                aggregate_type="Vehicle",
                aggregate_id=f"V_METRICS_{i}",
                event_type="VehicleCreated",
                data={"vehicle_number": f"LOC-{i}"}
            )
        db.commit()

        calculator = MetricsCalculator(db)
        metrics = PerformanceMetrics()

        metrics.start()

        # Calculate all KPIs
        availability = calculator.calculate_fleet_availability()
        mtbf = calculator.calculate_mtbf()
        mttr = calculator.calculate_mttr()
        completion_rate = calculator.calculate_workorder_completion_rate()
        turnover = calculator.calculate_inventory_turnover()
        stockout = calculator.calculate_stockout_rate()

        metrics.operations = 6  # 6 KPIs calculated
        metrics.stop()

        print(f"\n📊 Metrics Calculation Performance:")
        print(f"   KPIs calculated: {metrics.operations}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Avg per KPI: {metrics.duration / metrics.operations:.2f}s")

        assert metrics.duration < 5, "All KPIs should calculate in <5 seconds"

    def test_dashboard_generation_performance(self, db: Session):
        """Test dashboard generation performance"""
        dashboard_service = DashboardService(db)
        metrics = PerformanceMetrics()

        metrics.start()

        # Generate all dashboards
        exec_dashboard = dashboard_service.get_executive_dashboard()
        ops_dashboard = dashboard_service.get_operations_dashboard()
        maint_dashboard = dashboard_service.get_maintenance_dashboard()
        inv_dashboard = dashboard_service.get_inventory_dashboard()

        metrics.operations = 4  # 4 dashboards
        metrics.stop()

        print(f"\n📊 Dashboard Generation Performance:")
        print(f"   Dashboards: {metrics.operations}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Avg per dashboard: {metrics.duration / metrics.operations:.2f}s")

        assert metrics.duration < 10, "All dashboards should generate in <10 seconds"

        # Verify data structure
        assert "summary" in exec_dashboard
        assert "charts" in ops_dashboard
        assert len(maint_dashboard["charts"]) > 0

    def test_time_series_generation_performance(self, db: Session):
        """Test time series data generation performance"""
        event_store = EventStore(db)

        # Setup: Create events over 30 days
        base_time = datetime.utcnow() - timedelta(days=30)
        for day in range(30):
            for event_num in range(10):  # 10 events per day
                event_store.append_event(
                    aggregate_type="WorkOrder",
                    aggregate_id=f"WO_TS_D{day}_E{event_num}",
                    event_type="WorkOrderCreated",
                    data={"day": day, "event": event_num},
                    occurred_at=base_time + timedelta(days=day, hours=event_num)
                )
        db.commit()

        calculator = MetricsCalculator(db)
        metrics = PerformanceMetrics()

        metrics.start()

        # Generate time series for 30 days
        time_series = calculator.generate_event_time_series(
            "WorkOrderCreated",
            base_time,
            datetime.utcnow(),
            interval="day"
        )

        metrics.operations = len(time_series)
        metrics.stop()

        print(f"\n📊 Time Series Generation Performance:")
        print(f"   Data points: {metrics.operations}")
        print(f"   Duration: {metrics.duration:.2f}s")

        assert metrics.duration < 2, "Time series should generate in <2 seconds"
        assert len(time_series) > 0


class TestConcurrentOperations:
    """Test concurrent operation performance"""

    def test_concurrent_event_appends(self, db: Session):
        """Test concurrent event appending from multiple threads"""
        event_store = EventStore(db)
        metrics = PerformanceMetrics()

        def append_events(thread_id: int, count: int):
            """Append events from a thread"""
            local_errors = 0
            for i in range(count):
                try:
                    event_store.append_event(
                        aggregate_type="Vehicle",
                        aggregate_id=f"V_THREAD_{thread_id}_{i}",
                        event_type="VehicleCreated",
                        data={"thread": thread_id, "index": i}
                    )
                except Exception:
                    local_errors += 1
            return count - local_errors

        metrics.start()

        # Run 10 threads, each appending 50 events
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(append_events, i, 50) for i in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        db.commit()
        metrics.stop()

        metrics.operations = sum(results)
        metrics.errors = (10 * 50) - metrics.operations

        print(f"\n📊 Concurrent Event Append Performance:")
        print(f"   Threads: 10")
        print(f"   Total operations: {metrics.operations}")
        print(f"   Errors: {metrics.errors}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Throughput: {metrics.ops_per_second:.2f} events/sec")

        assert metrics.operations >= 450, "At least 90% success rate"
        assert metrics.ops_per_second > 50, "Concurrent throughput >50 ops/sec"

    def test_concurrent_metric_calculations(self, db: Session):
        """Test concurrent metric calculations"""
        calculator = MetricsCalculator(db)

        def calculate_metric(metric_name: str):
            """Calculate a metric"""
            start = time.time()
            if metric_name == "availability":
                result = calculator.calculate_fleet_availability()
            elif metric_name == "mtbf":
                result = calculator.calculate_mtbf()
            elif metric_name == "mttr":
                result = calculator.calculate_mttr()
            else:
                return 0
            return time.time() - start

        metrics = PerformanceMetrics()
        metrics.start()

        # Calculate multiple metrics concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(calculate_metric, "availability"),
                executor.submit(calculate_metric, "mtbf"),
                executor.submit(calculate_metric, "mttr"),
                executor.submit(calculate_metric, "availability"),
                executor.submit(calculate_metric, "mtbf"),
            ]
            durations = [f.result() for f in concurrent.futures.as_completed(futures)]

        metrics.stop()
        metrics.operations = len(durations)

        print(f"\n📊 Concurrent Metric Calculation Performance:")
        print(f"   Calculations: {metrics.operations}")
        print(f"   Total duration: {metrics.duration:.2f}s")
        print(f"   Avg per metric: {sum(durations) / len(durations):.2f}s")

        assert metrics.duration < 10, "Concurrent calculations should complete in <10s"


class TestSyncPerformance:
    """Test CRDT sync performance"""

    def test_sync_large_dataset(self, db: Session):
        """Test sync performance with large state dataset"""
        sync_engine = SyncEngine(db)
        metrics = PerformanceMetrics()

        # Prepare 1000 CRDT states to sync
        remote_states = []
        for i in range(1000):
            remote_states.append({
                "aggregate_type": "Vehicle",
                "aggregate_id": f"V_SYNC_{i}",
                "crdt_type": "LWW-Register",
                "state": {
                    "value": {"status": "active", "index": i},
                    "timestamp": datetime.utcnow().isoformat(),
                    "node_id": "remote-device"
                },
                "vector_clock": {"remote-device": 1}
            })

        metrics.start()

        # Perform sync
        result = sync_engine.sync_from_remote("local-device", remote_states)

        metrics.stop()
        metrics.operations = len(remote_states)

        print(f"\n📊 CRDT Sync Performance:")
        print(f"   States synced: {metrics.operations}")
        print(f"   Merged: {result.merged_count}")
        print(f"   Conflicts: {result.conflict_count}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Throughput: {metrics.ops_per_second:.2f} states/sec")

        assert metrics.duration < 30, "Sync of 1000 states should complete in <30s"
        assert result.merged_count > 0


class TestStressScenarios:
    """Test system under stress"""

    def test_stress_event_store(self, db: Session):
        """Stress test: Rapid event creation"""
        event_store = EventStore(db)
        metrics = PerformanceMetrics()

        metrics.start()

        # Rapidly create 5000 events
        for i in range(5000):
            try:
                event_store.append_event(
                    aggregate_type="Stress",
                    aggregate_id=f"STRESS_{i % 500}",
                    event_type="StressTestEvent",
                    data={"iteration": i, "timestamp": datetime.utcnow().isoformat()}
                )
                metrics.operations += 1
            except Exception:
                metrics.errors += 1

        db.commit()
        metrics.stop()

        print(f"\n🔥 Stress Test - Event Store:")
        print(f"   Target: 5000 events")
        print(f"   Created: {metrics.operations}")
        print(f"   Errors: {metrics.errors}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Throughput: {metrics.ops_per_second:.2f} events/sec")

        assert metrics.operations >= 4500, "At least 90% success under stress"

    def test_stress_analytics_queries(self, db: Session):
        """Stress test: Rapid analytics queries"""
        calculator = MetricsCalculator(db)
        metrics = PerformanceMetrics()

        metrics.start()

        # Perform 100 metric calculations rapidly
        for i in range(100):
            try:
                if i % 3 == 0:
                    calculator.calculate_fleet_availability()
                elif i % 3 == 1:
                    calculator.calculate_mtbf()
                else:
                    calculator.calculate_mttr()
                metrics.operations += 1
            except Exception:
                metrics.errors += 1

        metrics.stop()

        print(f"\n🔥 Stress Test - Analytics Queries:")
        print(f"   Target: 100 queries")
        print(f"   Completed: {metrics.operations}")
        print(f"   Errors: {metrics.errors}")
        print(f"   Duration: {metrics.duration:.2f}s")
        print(f"   Throughput: {metrics.ops_per_second:.2f} queries/sec")

        assert metrics.operations >= 90, "At least 90% success under stress"


@pytest.fixture
def db():
    """Database session fixture"""
    from src.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def print_summary():
    """Print performance test summary"""
    print("\n" + "=" * 80)
    print("  PERFORMANCE TEST SUMMARY")
    print("=" * 80)
    print("""
Performance Benchmarks:

Event Store:
  ✓ Bulk append: >10 events/sec
  ✓ Query: >20 queries/sec
  ✓ Replay: >100 events/sec

Analytics:
  ✓ All KPIs: <5 seconds
  ✓ All dashboards: <10 seconds
  ✓ Time series (30 days): <2 seconds

Concurrent Operations:
  ✓ Concurrent events: >50 events/sec
  ✓ Concurrent metrics: <10 seconds total

Sync:
  ✓ 1000 CRDT states: <30 seconds

Stress Tests:
  ✓ 5000 rapid events: ≥90% success
  ✓ 100 rapid queries: ≥90% success

All tests validate system can handle production load.
    """)


if __name__ == "__main__":
    print_summary()
