"""
Integration Tests - Event Sourcing Flow

End-to-end tests for event sourcing, projections, CRDT sync, and analytics.
Tests the complete flow from event creation to analytics dashboard.
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.railfleet.event import Event
from src.models.railfleet.vehicle import Vehicle
from src.models.railfleet.workorder import WorkOrder
from src.services.event_store import EventStore
from src.services.projections.vehicle_projection import VehicleProjection
from src.services.crdt.lww_register import LWWRegister
from src.services.sync_engine import SyncEngine
from src.services.analytics.metrics_calculator import MetricsCalculator
from src.services.analytics.dashboard_service import DashboardService


class TestEventSourcingFlow:
    """Test complete event sourcing flow"""

    def test_vehicle_lifecycle_with_events(self, db: Session):
        """
        Test vehicle lifecycle from creation to analytics.

        Flow:
        1. Create vehicle via event
        2. Apply projection
        3. Schedule maintenance via event
        4. Update CRDT state
        5. Sync to remote device
        6. Calculate metrics
        7. Generate dashboard
        """
        # 1. Create vehicle via event
        event_store = EventStore(db)

        vehicle_created = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V001",
            event_type="VehicleCreated",
            data={
                "vehicle_number": "LOC-001",
                "vehicle_type": "Locomotive",
                "status": "active",
                "location": "Depot A"
            },
            metadata={"user_id": "user123", "ip_address": "192.168.1.1"}
        )

        assert vehicle_created.id is not None
        assert vehicle_created.version == 1

        # 2. Apply projection
        projection_service = VehicleProjection(db)
        projection_service.handle_event(vehicle_created)

        db.commit()

        # Verify projection created vehicle
        vehicle = db.query(Vehicle).filter_by(id="V001").first()
        assert vehicle is not None
        assert vehicle.vehicle_number == "LOC-001"
        assert vehicle.status == "active"

        # 3. Schedule maintenance via event
        maintenance_event = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V001",
            event_type="VehicleMaintenanceScheduled",
            data={
                "maintenance_type": "routine",
                "scheduled_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "priority": "medium"
            },
            metadata={"user_id": "user123"}
        )

        assert maintenance_event.version == 2

        # 4. Update CRDT state
        crdt = LWWRegister(value={"status": "maintenance"}, timestamp=datetime.utcnow())
        crdt_state = crdt.to_dict()

        assert crdt_state["value"]["status"] == "maintenance"

        # 5. Sync to remote device
        sync_engine = SyncEngine(db)
        local_device_id = "device-001"
        remote_device_id = "device-002"

        # Push local state to remote
        local_states = [
            {
                "aggregate_type": "Vehicle",
                "aggregate_id": "V001",
                "crdt_type": "LWW-Register",
                "state": crdt_state,
                "vector_clock": {"device-001": 1}
            }
        ]

        sync_result = sync_engine.sync_from_remote(remote_device_id, local_states)

        assert sync_result.merged_count > 0
        assert sync_result.conflict_count == 0  # No conflicts expected

        # 6. Calculate metrics
        calculator = MetricsCalculator(db)

        # Fleet availability should reflect the vehicle
        availability = calculator.calculate_fleet_availability()
        assert availability.value >= 0
        assert availability.value <= 100

        # MTBF calculation
        mtbf = calculator.calculate_mtbf()
        assert mtbf.value >= 0
        assert mtbf.unit == "hours"

        # 7. Generate dashboard
        dashboard_service = DashboardService(db)
        dashboard = dashboard_service.get_executive_dashboard()

        assert "summary" in dashboard
        assert "fleet" in dashboard["summary"]
        assert dashboard["summary"]["fleet"]["total_vehicles"] > 0
        assert len(dashboard["charts"]) > 0
        assert "insights" in dashboard

    def test_workorder_completion_flow(self, db: Session):
        """
        Test work order from creation to completion with analytics.

        Flow:
        1. Create work order via event
        2. Apply projection
        3. Complete work order via event
        4. Calculate completion rate
        5. Generate operations dashboard
        """
        event_store = EventStore(db)

        # Create vehicle first
        vehicle_event = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V002",
            event_type="VehicleCreated",
            data={"vehicle_number": "LOC-002", "status": "active"}
        )

        # Apply vehicle projection
        VehicleProjection(db).handle_event(vehicle_event)
        db.commit()

        # 1. Create work order
        wo_created = event_store.append_event(
            aggregate_type="WorkOrder",
            aggregate_id="WO001",
            event_type="WorkOrderCreated",
            data={
                "vehicle_id": "V002",
                "description": "Routine maintenance",
                "priority": "medium",
                "estimated_cost": 500
            },
            metadata={"user_id": "user456"}
        )

        assert wo_created.version == 1

        # 2. Apply projection
        from src.services.projections.workorder_projection import WorkOrderProjection
        WorkOrderProjection(db).handle_event(wo_created)
        db.commit()

        # Verify work order created
        wo = db.query(WorkOrder).filter_by(id="WO001").first()
        assert wo is not None
        assert wo.status == "pending"
        assert wo.priority == "medium"

        # 3. Complete work order
        wo_completed = event_store.append_event(
            aggregate_type="WorkOrder",
            aggregate_id="WO001",
            event_type="WorkOrderCompleted",
            data={
                "actual_cost": 475,
                "completion_notes": "Completed successfully"
            },
            metadata={"user_id": "user456"}
        )

        WorkOrderProjection(db).handle_event(wo_completed)
        db.commit()

        wo = db.query(WorkOrder).filter_by(id="WO001").first()
        assert wo.status == "completed"

        # 4. Calculate completion rate
        calculator = MetricsCalculator(db)
        completion_rate = calculator.calculate_workorder_completion_rate()

        assert completion_rate.value >= 0
        assert completion_rate.value <= 100
        assert completion_rate.unit == "%"

        # 5. Generate operations dashboard
        dashboard_service = DashboardService(db)
        ops_dashboard = dashboard_service.get_operations_dashboard()

        assert "operations" in ops_dashboard
        assert "active_workorders" in ops_dashboard["operations"]
        assert "charts" in ops_dashboard
        assert len(ops_dashboard["charts"]) > 0

    def test_time_travel_query_integration(self, db: Session):
        """
        Test time-travel queries on event history.

        Flow:
        1. Create events at different timestamps
        2. Query state at specific time points
        3. Verify state reconstruction
        """
        event_store = EventStore(db)

        base_time = datetime.utcnow()

        # Event 1: Create vehicle
        event1 = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V003",
            event_type="VehicleCreated",
            data={"vehicle_number": "LOC-003", "status": "active"},
            occurred_at=base_time
        )

        # Event 2: Update status (1 hour later)
        event2 = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V003",
            event_type="VehicleStatusChanged",
            data={"old_status": "active", "new_status": "maintenance"},
            occurred_at=base_time + timedelta(hours=1)
        )

        # Event 3: Update status again (2 hours later)
        event3 = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V003",
            event_type="VehicleStatusChanged",
            data={"old_status": "maintenance", "new_status": "active"},
            occurred_at=base_time + timedelta(hours=2)
        )

        # Query state at different time points
        from src.services.time_travel import TimeTravelQuery, TimePoint

        time_travel = TimeTravelQuery(db)

        # State at creation time
        state_t0 = time_travel.get_state_at(
            "Vehicle",
            "V003",
            TimePoint(timestamp=base_time + timedelta(minutes=1))
        )
        assert state_t0 is not None
        assert state_t0.data["status"] == "active"
        assert state_t0.version == 1

        # State after first update
        state_t1 = time_travel.get_state_at(
            "Vehicle",
            "V003",
            TimePoint(timestamp=base_time + timedelta(hours=1, minutes=30))
        )
        assert state_t1.data["status"] == "maintenance"
        assert state_t1.version == 2

        # State after second update
        state_t2 = time_travel.get_state_at(
            "Vehicle",
            "V003",
            TimePoint(timestamp=base_time + timedelta(hours=3))
        )
        assert state_t2.data["status"] == "active"
        assert state_t2.version == 3

    def test_ml_prediction_integration(self, db: Session):
        """
        Test ML pipeline integration.

        Flow:
        1. Create events with vehicle history
        2. Extract features
        3. Make prediction
        4. Store prediction result
        """
        from src.services.ml.feature_engineering import FeatureEngineering
        from src.services.ml.models.maintenance_predictor import MaintenancePredictor
        from src.services.ml.model_metadata import ModelMetadata

        event_store = EventStore(db)

        # Create vehicle with history
        event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V004",
            event_type="VehicleCreated",
            data={
                "vehicle_number": "LOC-004",
                "status": "active",
                "age_days": 1825,  # 5 years
                "mileage": 150000
            }
        )

        # Add maintenance history
        for i in range(5):
            event_store.append_event(
                aggregate_type="Vehicle",
                aggregate_id="V004",
                event_type="MaintenanceCompleted",
                data={
                    "maintenance_type": "routine",
                    "date": (datetime.utcnow() - timedelta(days=90 * i)).isoformat()
                }
            )

        db.commit()

        # Extract features
        feature_eng = FeatureEngineering(db)
        features = feature_eng.extract_vehicle_features("V004")

        assert features is not None
        assert len(features.features) > 0
        assert "age_days" in features.features
        assert features.features["age_days"] >= 0

        # Make prediction (with mock model)
        metadata = ModelMetadata(
            model_name="maintenance_predictor",
            version="1.0.0",
            model_type="classification",
            target="needs_maintenance",
            features=list(features.features.keys())
        )

        predictor = MaintenancePredictor(metadata)

        # Note: Actual prediction requires trained model
        # This test verifies the integration structure
        assert predictor.model_name == "maintenance_predictor"

    def test_analytics_time_series_integration(self, db: Session):
        """
        Test time series generation for analytics charts.

        Flow:
        1. Create events over time
        2. Generate time series data
        3. Verify data structure for charting
        """
        event_store = EventStore(db)
        base_time = datetime.utcnow() - timedelta(days=7)

        # Create events over 7 days
        for day in range(7):
            event_time = base_time + timedelta(days=day)

            # Create 2-5 work orders per day
            for wo_num in range(2 + (day % 4)):
                event_store.append_event(
                    aggregate_type="WorkOrder",
                    aggregate_id=f"WO-DAY{day}-{wo_num}",
                    event_type="WorkOrderCreated",
                    data={"description": f"Work order {wo_num}", "priority": "medium"},
                    occurred_at=event_time
                )

        db.commit()

        # Generate time series
        calculator = MetricsCalculator(db)
        time_series = calculator.generate_event_time_series(
            "WorkOrderCreated",
            base_time,
            datetime.utcnow(),
            interval="day"
        )

        assert len(time_series) > 0

        # Verify data structure
        for data_point in time_series:
            assert hasattr(data_point, "timestamp")
            assert hasattr(data_point, "value")
            assert data_point.value >= 0

        # Verify chart-ready format
        chart_data = [dp.to_dict() for dp in time_series]
        assert all("timestamp" in dp for dp in chart_data)
        assert all("value" in dp for dp in chart_data)

    def test_compliance_report_integration(self, db: Session):
        """
        Test compliance reporting integration.

        Flow:
        1. Create events with user attribution
        2. Generate GDPR compliance report
        3. Verify audit completeness
        """
        from src.services.compliance_reporter import ComplianceReporter

        event_store = EventStore(db)

        # Create events with proper attribution
        for i in range(10):
            event_store.append_event(
                aggregate_type="Vehicle",
                aggregate_id=f"V{100+i}",
                event_type="VehicleCreated",
                data={"vehicle_number": f"LOC-{100+i}"},
                metadata={
                    "user_id": f"user{i % 3}",  # Rotate users
                    "ip_address": "192.168.1.1"
                }
            )

        db.commit()

        # Generate compliance report
        reporter = ComplianceReporter(db)
        gdpr_report = reporter.generate_gdpr_report(
            start_date=datetime.utcnow() - timedelta(days=1),
            end_date=datetime.utcnow(),
            scope="all"
        )

        assert gdpr_report.report_type == "GDPR"
        assert gdpr_report.status in ["pass", "fail", "warning"]
        assert len(gdpr_report.checks) > 0

        # Verify audit trail check
        audit_check = next(
            (c for c in gdpr_report.checks if c.check_name == "audit_trail_completeness"),
            None
        )
        assert audit_check is not None
        assert audit_check.passed is True  # All events have metadata


class TestConcurrency:
    """Test concurrent operations"""

    def test_concurrent_event_append(self, db: Session):
        """Test concurrent event appending with version control"""
        event_store = EventStore(db)

        # Create initial event
        event1 = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V_CONCURRENT",
            event_type="VehicleCreated",
            data={"vehicle_number": "CONCURRENT-001"}
        )

        assert event1.version == 1

        # Simulate concurrent updates
        event2 = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V_CONCURRENT",
            event_type="VehicleStatusChanged",
            data={"status": "maintenance"}
        )

        event3 = event_store.append_event(
            aggregate_type="Vehicle",
            aggregate_id="V_CONCURRENT",
            event_type="VehicleLocationChanged",
            data={"location": "Workshop A"}
        )

        # Verify versions are sequential
        assert event2.version == 2
        assert event3.version == 3

    def test_crdt_conflict_resolution(self, db: Session):
        """Test CRDT automatic conflict resolution"""
        from src.services.crdt.lww_register import LWWRegister

        # Two devices update the same field
        device1_time = datetime.utcnow()
        device2_time = device1_time + timedelta(seconds=1)  # Device 2 is later

        register1 = LWWRegister(value={"status": "active"}, timestamp=device1_time)
        register2 = LWWRegister(value={"status": "maintenance"}, timestamp=device2_time)

        # Merge: later timestamp wins
        merged = register1.merge(register2)

        assert merged.value["status"] == "maintenance"  # Device 2's value (later)


@pytest.fixture
def db():
    """Database session fixture"""
    from src.database import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        # Cleanup
        session.rollback()
        session.close()
