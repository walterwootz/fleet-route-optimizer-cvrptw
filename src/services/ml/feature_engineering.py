"""Feature Engineering - Extract ML features from event data.

Transforms event sourcing data into feature vectors for machine learning models.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from ...models.railfleet.events import Event as EventModel
from ...models.railfleet import Vehicle, WorkOrder, Part, StockMove
from ...config import get_logger

logger = get_logger(__name__)


class FeatureVector:
    """Feature vector with metadata."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        features: Dict[str, float],
        feature_names: List[str],
        timestamp: datetime,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.features = features
        self.feature_names = feature_names
        self.timestamp = timestamp

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for ML models."""
        return np.array([self.features[name] for name in self.feature_names])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "features": self.features,
            "feature_names": self.feature_names,
            "timestamp": self.timestamp.isoformat(),
        }


class FeatureEngineering:
    """Service for extracting ML features from event data.

    Example:
        >>> fe = FeatureEngineering(db)
        >>>
        >>> # Extract vehicle maintenance features
        >>> features = fe.extract_vehicle_features("V001")
        >>> print(f"Feature vector: {features.to_array()}")
        >>>
        >>> # Extract work order features
        >>> features = fe.extract_workorder_features("WO123")
        >>> print(f"Completion probability: {features.features['completion_score']}")
    """

    def __init__(self, db: Session):
        self.db = db

    def extract_vehicle_features(
        self,
        vehicle_id: str,
        as_of: Optional[datetime] = None,
    ) -> FeatureVector:
        """Extract features for vehicle maintenance prediction.

        Features:
        - Age (days since first event)
        - Mileage
        - Event count (total)
        - Maintenance count (last 90 days)
        - Days since last maintenance
        - Average days between maintenance
        - Critical event count (last 30 days)
        - Status duration (days in current status)

        Args:
            vehicle_id: Vehicle identifier
            as_of: Extract features as of this timestamp (default: now)

        Returns:
            FeatureVector with vehicle features
        """
        if as_of is None:
            as_of = datetime.utcnow()

        # Get vehicle events up to timestamp
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == "Vehicle",
                    EventModel.aggregate_id == vehicle_id,
                    EventModel.occurred_at <= as_of,
                )
            )
            .order_by(EventModel.occurred_at)
            .all()
        )

        if not events:
            logger.warning(f"No events found for vehicle {vehicle_id}")
            return self._empty_vehicle_features(vehicle_id, as_of)

        # Calculate features
        features = {}

        # Age (days since first event)
        first_event = events[0]
        features["age_days"] = (as_of - first_event.occurred_at).days

        # Mileage (from latest event)
        mileage = 0
        for event in reversed(events):
            if event.data and "mileage" in event.data:
                mileage = event.data["mileage"]
                break
        features["mileage"] = float(mileage)

        # Event count
        features["event_count"] = float(len(events))

        # Maintenance-related events
        maintenance_events = [
            e for e in events
            if "maintenance" in e.event_type.lower()
        ]
        features["maintenance_count_total"] = float(len(maintenance_events))

        # Recent maintenance (last 90 days)
        recent_cutoff = as_of - timedelta(days=90)
        recent_maintenance = [
            e for e in maintenance_events
            if e.occurred_at >= recent_cutoff
        ]
        features["maintenance_count_90d"] = float(len(recent_maintenance))

        # Days since last maintenance
        if maintenance_events:
            last_maintenance = maintenance_events[-1]
            features["days_since_maintenance"] = (
                as_of - last_maintenance.occurred_at
            ).days
        else:
            features["days_since_maintenance"] = 999.0  # No maintenance yet

        # Average days between maintenance
        if len(maintenance_events) > 1:
            time_spans = []
            for i in range(1, len(maintenance_events)):
                span = (
                    maintenance_events[i].occurred_at
                    - maintenance_events[i - 1].occurred_at
                ).days
                time_spans.append(span)
            features["avg_days_between_maintenance"] = np.mean(time_spans)
        else:
            features["avg_days_between_maintenance"] = 0.0

        # Critical events (last 30 days)
        critical_cutoff = as_of - timedelta(days=30)
        critical_events = [
            e for e in events
            if e.occurred_at >= critical_cutoff
            and any(
                keyword in e.event_type.lower()
                for keyword in ["critical", "failure", "breakdown"]
            )
        ]
        features["critical_event_count_30d"] = float(len(critical_events))

        # Status duration (days in current status)
        current_status = None
        status_changed_at = first_event.occurred_at

        for event in events:
            if event.data and "status" in event.data:
                current_status = event.data["status"]
                status_changed_at = event.occurred_at

        if current_status:
            features["status_duration_days"] = (as_of - status_changed_at).days
        else:
            features["status_duration_days"] = 0.0

        # Feature names in order
        feature_names = [
            "age_days",
            "mileage",
            "event_count",
            "maintenance_count_total",
            "maintenance_count_90d",
            "days_since_maintenance",
            "avg_days_between_maintenance",
            "critical_event_count_30d",
            "status_duration_days",
        ]

        logger.info(f"Extracted {len(features)} features for vehicle {vehicle_id}")

        return FeatureVector(
            entity_type="Vehicle",
            entity_id=vehicle_id,
            features=features,
            feature_names=feature_names,
            timestamp=as_of,
        )

    def extract_workorder_features(
        self,
        workorder_id: str,
        as_of: Optional[datetime] = None,
    ) -> FeatureVector:
        """Extract features for work order completion prediction.

        Features:
        - Priority (numeric encoding)
        - Task count
        - Assigned staff count
        - Days since created
        - Days since started
        - Parts required count
        - Estimated hours
        - Status changes count

        Args:
            workorder_id: Work order identifier
            as_of: Extract features as of this timestamp

        Returns:
            FeatureVector with work order features
        """
        if as_of is None:
            as_of = datetime.utcnow()

        # Get work order events
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == "WorkOrder",
                    EventModel.aggregate_id == workorder_id,
                    EventModel.occurred_at <= as_of,
                )
            )
            .order_by(EventModel.occurred_at)
            .all()
        )

        if not events:
            return self._empty_workorder_features(workorder_id, as_of)

        # Calculate features
        features = {}

        # Priority (encode as numeric)
        priority_map = {"low": 1.0, "normal": 2.0, "high": 3.0, "critical": 4.0}
        priority = "normal"
        for event in reversed(events):
            if event.data and "priority" in event.data:
                priority = event.data["priority"]
                break
        features["priority_numeric"] = priority_map.get(priority, 2.0)

        # Task count
        tasks = set()
        for event in events:
            if event.data and "tasks" in event.data:
                tasks.update(event.data["tasks"])
        features["task_count"] = float(len(tasks))

        # Assigned staff count
        staff = set()
        for event in events:
            if event.data and "assigned_staff" in event.data:
                staff.update(event.data["assigned_staff"])
        features["assigned_staff_count"] = float(len(staff))

        # Days since created
        created_at = events[0].occurred_at
        features["days_since_created"] = (as_of - created_at).days

        # Days since started
        started_at = None
        for event in events:
            if "started" in event.event_type.lower():
                started_at = event.occurred_at
                break

        if started_at:
            features["days_since_started"] = (as_of - started_at).days
        else:
            features["days_since_started"] = 0.0

        # Parts required count
        parts_required = 0
        for event in events:
            if event.data and "parts_required" in event.data:
                parts_required = len(event.data["parts_required"])
                break
        features["parts_required_count"] = float(parts_required)

        # Estimated hours
        estimated_hours = 0.0
        for event in events:
            if event.data and "estimated_hours" in event.data:
                estimated_hours = float(event.data["estimated_hours"])
                break
        features["estimated_hours"] = estimated_hours

        # Status changes count
        status_changes = [
            e for e in events if "status" in e.event_type.lower()
        ]
        features["status_changes_count"] = float(len(status_changes))

        feature_names = [
            "priority_numeric",
            "task_count",
            "assigned_staff_count",
            "days_since_created",
            "days_since_started",
            "parts_required_count",
            "estimated_hours",
            "status_changes_count",
        ]

        return FeatureVector(
            entity_type="WorkOrder",
            entity_id=workorder_id,
            features=features,
            feature_names=feature_names,
            timestamp=as_of,
        )

    def extract_inventory_features(
        self,
        part_id: str,
        as_of: Optional[datetime] = None,
    ) -> FeatureVector:
        """Extract features for inventory demand prediction.

        Features:
        - Average usage (last 30 days)
        - Usage variance
        - Stock moves count (last 90 days)
        - Days since last usage
        - Seasonal pattern (day of week, month)

        Args:
            part_id: Part identifier
            as_of: Extract features as of this timestamp

        Returns:
            FeatureVector with inventory features
        """
        if as_of is None:
            as_of = datetime.utcnow()

        # Get stock move events for part
        events = (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == "StockMove",
                    EventModel.occurred_at <= as_of,
                )
            )
            .order_by(EventModel.occurred_at)
            .all()
        )

        # Filter events for this part
        part_events = [
            e for e in events
            if e.data and e.data.get("part_id") == part_id
        ]

        if not part_events:
            return self._empty_inventory_features(part_id, as_of)

        features = {}

        # Usage in last 30 days
        cutoff_30d = as_of - timedelta(days=30)
        recent_moves = [e for e in part_events if e.occurred_at >= cutoff_30d]

        if recent_moves:
            quantities = [
                abs(e.data.get("quantity", 0))
                for e in recent_moves
                if e.data
            ]
            features["avg_usage_30d"] = np.mean(quantities) if quantities else 0.0
            features["usage_variance"] = np.var(quantities) if quantities else 0.0
        else:
            features["avg_usage_30d"] = 0.0
            features["usage_variance"] = 0.0

        # Stock moves count (last 90 days)
        cutoff_90d = as_of - timedelta(days=90)
        moves_90d = [e for e in part_events if e.occurred_at >= cutoff_90d]
        features["moves_count_90d"] = float(len(moves_90d))

        # Days since last usage
        if part_events:
            last_event = part_events[-1]
            features["days_since_usage"] = (as_of - last_event.occurred_at).days
        else:
            features["days_since_usage"] = 999.0

        # Seasonal patterns
        features["day_of_week"] = float(as_of.weekday())  # 0=Monday, 6=Sunday
        features["month"] = float(as_of.month)  # 1-12

        feature_names = [
            "avg_usage_30d",
            "usage_variance",
            "moves_count_90d",
            "days_since_usage",
            "day_of_week",
            "month",
        ]

        return FeatureVector(
            entity_type="Part",
            entity_id=part_id,
            features=features,
            feature_names=feature_names,
            timestamp=as_of,
        )

    def extract_batch_features(
        self,
        entity_type: str,
        entity_ids: List[str],
        as_of: Optional[datetime] = None,
    ) -> List[FeatureVector]:
        """Extract features for multiple entities.

        Args:
            entity_type: Type of entity (Vehicle, WorkOrder, Part)
            entity_ids: List of entity identifiers
            as_of: Extract features as of this timestamp

        Returns:
            List of FeatureVector objects
        """
        feature_vectors = []

        for entity_id in entity_ids:
            try:
                if entity_type == "Vehicle":
                    fv = self.extract_vehicle_features(entity_id, as_of)
                elif entity_type == "WorkOrder":
                    fv = self.extract_workorder_features(entity_id, as_of)
                elif entity_type == "Part":
                    fv = self.extract_inventory_features(entity_id, as_of)
                else:
                    logger.warning(f"Unknown entity type: {entity_type}")
                    continue

                feature_vectors.append(fv)

            except Exception as e:
                logger.error(
                    f"Failed to extract features for {entity_type}:{entity_id}: {e}"
                )

        logger.info(
            f"Extracted features for {len(feature_vectors)}/{len(entity_ids)} entities"
        )

        return feature_vectors

    def _empty_vehicle_features(
        self, vehicle_id: str, timestamp: datetime
    ) -> FeatureVector:
        """Return empty feature vector for vehicle."""
        return FeatureVector(
            entity_type="Vehicle",
            entity_id=vehicle_id,
            features={
                "age_days": 0.0,
                "mileage": 0.0,
                "event_count": 0.0,
                "maintenance_count_total": 0.0,
                "maintenance_count_90d": 0.0,
                "days_since_maintenance": 999.0,
                "avg_days_between_maintenance": 0.0,
                "critical_event_count_30d": 0.0,
                "status_duration_days": 0.0,
            },
            feature_names=[
                "age_days",
                "mileage",
                "event_count",
                "maintenance_count_total",
                "maintenance_count_90d",
                "days_since_maintenance",
                "avg_days_between_maintenance",
                "critical_event_count_30d",
                "status_duration_days",
            ],
            timestamp=timestamp,
        )

    def _empty_workorder_features(
        self, workorder_id: str, timestamp: datetime
    ) -> FeatureVector:
        """Return empty feature vector for work order."""
        return FeatureVector(
            entity_type="WorkOrder",
            entity_id=workorder_id,
            features={
                "priority_numeric": 2.0,
                "task_count": 0.0,
                "assigned_staff_count": 0.0,
                "days_since_created": 0.0,
                "days_since_started": 0.0,
                "parts_required_count": 0.0,
                "estimated_hours": 0.0,
                "status_changes_count": 0.0,
            },
            feature_names=[
                "priority_numeric",
                "task_count",
                "assigned_staff_count",
                "days_since_created",
                "days_since_started",
                "parts_required_count",
                "estimated_hours",
                "status_changes_count",
            ],
            timestamp=timestamp,
        )

    def _empty_inventory_features(
        self, part_id: str, timestamp: datetime
    ) -> FeatureVector:
        """Return empty feature vector for inventory."""
        return FeatureVector(
            entity_type="Part",
            entity_id=part_id,
            features={
                "avg_usage_30d": 0.0,
                "usage_variance": 0.0,
                "moves_count_90d": 0.0,
                "days_since_usage": 999.0,
                "day_of_week": float(timestamp.weekday()),
                "month": float(timestamp.month),
            },
            feature_names=[
                "avg_usage_30d",
                "usage_variance",
                "moves_count_90d",
                "days_since_usage",
                "day_of_week",
                "month",
            ],
            timestamp=timestamp,
        )
