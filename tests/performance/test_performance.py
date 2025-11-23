"""
Performance Tests for RailFleet Manager

Test Goals:
- Scheduler with 100+ Work Orders
- Sync with 1000+ Events
- Stock aggregation with 10,000+ Moves
"""
import pytest
import time
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from src.app import app

client = TestClient(app)


@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Performance benchmarks for RailFleet Manager."""

    def test_bulk_part_creation(self, test_db, auth_headers):
        """Test creating 100 parts in bulk."""
        start_time = time.time()
        created_count = 0

        for i in range(100):
            part_data = {
                "part_no": f"PERF-PART-{i:04d}",
                "name": f"Performance Test Part {i}",
                "railway_class": "STANDARD",
                "unit": "pc",
                "min_stock": 5,
                "current_stock": 10,
                "unit_price": 50.00 + i,
                "is_active": True
            }
            response = client.post("/api/v1/parts", json=part_data, headers=auth_headers)
            if response.status_code == 201:
                created_count += 1

        elapsed_time = time.time() - start_time

        assert created_count == 100
        assert elapsed_time < 30  # Should complete in less than 30 seconds

        print(f"\n✅ Created {created_count} parts in {elapsed_time:.2f}s")
        print(f"   Average: {elapsed_time/created_count*1000:.2f}ms per part")

    def test_bulk_stock_moves(self, test_db, auth_headers, sample_part, sample_location):
        """Test creating 1000 stock moves."""
        if not sample_part or not sample_location:
            pytest.skip("Sample fixtures not available")

        start_time = time.time()
        created_count = 0

        for i in range(1000):
            move_data = {
                "part_no": sample_part["part_no"],
                "move_type": "INCOMING" if i % 2 == 0 else "USAGE",
                "quantity": 1,
                "to_location_id": sample_location["id"] if i % 2 == 0 else None,
                "from_location_id": sample_location["id"] if i % 2 == 1 else None,
                "reference_doc": f"PERF-TEST-{i:04d}",
                "unit_price": 50.00
            }
            response = client.post("/api/v1/stock/moves", json=move_data, headers=auth_headers)
            if response.status_code == 201:
                created_count += 1

            # Check progress every 100
            if (i + 1) % 100 == 0:
                elapsed = time.time() - start_time
                print(f"   Progress: {i+1}/1000 moves ({elapsed:.1f}s)")

        elapsed_time = time.time() - start_time

        assert created_count == 1000
        assert elapsed_time < 120  # Should complete in less than 2 minutes

        print(f"\n✅ Created {created_count} stock moves in {elapsed_time:.2f}s")
        print(f"   Average: {elapsed_time/created_count*1000:.2f}ms per move")
        print(f"   Throughput: {created_count/elapsed_time:.2f} moves/sec")

    def test_stock_overview_aggregation(self, test_db, auth_headers):
        """Test stock overview aggregation performance with large dataset."""
        # This test assumes bulk_stock_moves has run and created data
        start_time = time.time()

        response = client.get("/api/v1/stock/overview", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 5  # Should complete in less than 5 seconds

        overview = response.json()
        print(f"\n✅ Stock overview aggregation completed in {elapsed_time:.2f}s")
        print(f"   Items: {overview['total_items']}")

    def test_budget_overview_with_many_entries(self, test_db, auth_headers):
        """Test budget overview with multiple cost centers."""
        # Create 50 budget entries
        period = datetime.utcnow().strftime("%Y-%m")
        created_count = 0

        for i in range(50):
            budget_data = {
                "period": period,
                "cost_center": f"PERF-CC-{i:03d}",
                "category": "PARTS" if i % 2 == 0 else "LABOR",
                "planned_amount": 10000 + (i * 100),
                "forecast_amount": 9500 + (i * 100),
                "actual_amount": 8000 + (i * 100)
            }
            response = client.post("/api/v1/budget", json=budget_data, headers=auth_headers)
            if response.status_code == 201:
                created_count += 1

        print(f"   Created {created_count} budget entries")

        # Test overview performance
        start_time = time.time()
        response = client.get(f"/api/v1/budget/overview?period={period}", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 3  # Should complete in less than 3 seconds

        overview = response.json()
        print(f"\n✅ Budget overview completed in {elapsed_time:.2f}s")
        print(f"   Cost centers: {len(overview['items'])}")

    def test_parts_usage_report_performance(self, test_db, auth_headers):
        """Test parts usage report performance."""
        period = datetime.utcnow().strftime("%Y-%m")

        start_time = time.time()
        response = client.get(f"/api/v1/reports/parts_usage?period={period}", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 5  # Should complete in less than 5 seconds

        report = response.json()
        print(f"\n✅ Parts usage report completed in {elapsed_time:.2f}s")
        print(f"   Parts analyzed: {len(report['metrics'])}")
        print(f"   Total quantity: {report['total_quantity']}")

    def test_cost_report_performance(self, test_db, auth_headers):
        """Test cost report performance."""
        period = datetime.utcnow().strftime("%Y-%m")

        start_time = time.time()
        response = client.get(f"/api/v1/reports/costs?period={period}", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 3  # Should complete in less than 3 seconds

        report = response.json()
        print(f"\n✅ Cost report completed in {elapsed_time:.2f}s")
        print(f"   Cost centers: {len(report['metrics'])}")

    def test_dashboard_summary_performance(self, test_db, auth_headers):
        """Test dashboard summary aggregation performance."""
        period = datetime.utcnow().strftime("%Y-%m")

        start_time = time.time()
        response = client.get(f"/api/v1/reports/dashboard?period={period}", headers=auth_headers)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 5  # Should complete in less than 5 seconds

        dashboard = response.json()
        print(f"\n✅ Dashboard summary completed in {elapsed_time:.2f}s")
        print(f"   Availability: {dashboard['availability_pct']}%")
        print(f"   On-time ratio: {dashboard['on_time_ratio_pct']}%")
        print(f"   Budget utilization: {dashboard['budget_utilization_pct']}%")


@pytest.mark.performance
class TestConcurrentOperations:
    """Test concurrent operations performance."""

    def test_concurrent_part_reads(self, test_db, auth_headers):
        """Test reading parts list concurrently."""
        import concurrent.futures

        def fetch_parts():
            return client.get("/api/v1/parts?limit=100", headers=auth_headers)

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_parts) for _ in range(50)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        elapsed_time = time.time() - start_time

        successful = sum(1 for r in results if r.status_code == 200)
        assert successful == 50

        print(f"\n✅ {successful} concurrent requests completed in {elapsed_time:.2f}s")
        print(f"   Average: {elapsed_time/50*1000:.2f}ms per request")
        print(f"   Throughput: {50/elapsed_time:.2f} requests/sec")


# Performance Benchmarks Documentation
PERFORMANCE_BENCHMARKS = """
Performance Benchmarks for RailFleet Manager
============================================

Target Metrics:
- Part creation: < 300ms per part
- Stock move creation: < 150ms per move
- Stock overview aggregation: < 5s (with 10,000+ moves)
- Budget overview: < 3s (with 50+ cost centers)
- Reports: < 5s per report
- Concurrent reads: > 10 requests/sec

Test Results: (Run with: pytest tests/performance -v -s)
"""
