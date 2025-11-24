"""Time-Travel Query Service - Point-in-time state reconstruction.

Enables querying entity state at any point in time by replaying events
from the event store.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.railfleet.events import Event as EventModel
from ..models.events.base import BaseEvent, AggregateRoot
from ..services.event_store import EventStore
from ..config import get_logger

logger = get_logger(__name__)


class TimePoint:
    """Represents a point in time for queries.

    Can be specified as:
    - Absolute timestamp
    - Relative offset (e.g., "1 hour ago")
    - Event version number
    """

    def __init__(
        self,
        timestamp: Optional[datetime] = None,
        version: Optional[int] = None,
    ):
        self.timestamp = timestamp
        self.version = version

    @classmethod
    def now(cls) -> "TimePoint":
        """Create a TimePoint for current time."""
        return cls(timestamp=datetime.utcnow())

    @classmethod
    def at_timestamp(cls, timestamp: datetime) -> "TimePoint":
        """Create a TimePoint at specific timestamp."""
        return cls(timestamp=timestamp)

    @classmethod
    def at_version(cls, version: int) -> "TimePoint":
        """Create a TimePoint at specific version."""
        return cls(version=version)

    def __repr__(self):
        if self.timestamp:
            return f"<TimePoint at {self.timestamp.isoformat()}>"
        elif self.version:
            return f"<TimePoint at version {self.version}>"
        return "<TimePoint undefined>"


class StateSnapshot:
    """Snapshot of entity state at a point in time."""

    def __init__(
        self,
        aggregate_id: str,
        aggregate_type: str,
        state: Dict[str, Any],
        version: int,
        timestamp: datetime,
        event_count: int,
    ):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.state = state
        self.version = version
        self.timestamp = timestamp
        self.event_count = event_count

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "state": self.state,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "event_count": self.event_count,
        }


class TimeTravelQuery:
    """Service for time-travel queries over event history.

    Reconstructs entity state at any point in time by replaying events.

    Example:
        >>> query = TimeTravelQuery(db)
        >>> # Get vehicle state yesterday
        >>> snapshot = query.get_state_at(
        ...     "Vehicle", "V001",
        ...     TimePoint.at_timestamp(yesterday)
        ... )
        >>> print(f"Status yesterday: {snapshot.state['status']}")
        >>>
        >>> # Get state at version 5
        >>> snapshot = query.get_state_at(
        ...     "Vehicle", "V001",
        ...     TimePoint.at_version(5)
        ... )
    """

    def __init__(self, db: Session):
        self.db = db
        self.event_store = EventStore(db)

    def get_state_at(
        self,
        aggregate_type: str,
        aggregate_id: str,
        time_point: TimePoint,
    ) -> Optional[StateSnapshot]:
        """Get entity state at a specific point in time.

        Args:
            aggregate_type: Type of aggregate (e.g., "Vehicle", "WorkOrder")
            aggregate_id: Aggregate identifier
            time_point: Point in time to query

        Returns:
            StateSnapshot at that time or None if not found
        """
        # Get events up to the time point
        if time_point.timestamp:
            events = self._get_events_until_timestamp(
                aggregate_type, aggregate_id, time_point.timestamp
            )
        elif time_point.version is not None:
            events = self._get_events_until_version(
                aggregate_type, aggregate_id, time_point.version
            )
        else:
            logger.error("TimePoint must specify either timestamp or version")
            return None

        if not events:
            logger.info(f"No events found for {aggregate_type}:{aggregate_id}")
            return None

        # Replay events to reconstruct state
        state = self._replay_events(events)

        # Get last event for metadata
        last_event = events[-1]

        return StateSnapshot(
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            state=state,
            version=last_event.aggregate_version,
            timestamp=last_event.occurred_at,
            event_count=len(events),
        )

    def get_state_history(
        self,
        aggregate_type: str,
        aggregate_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[StateSnapshot]:
        """Get state history with snapshots at each event.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            start_time: Start of time range (optional)
            end_time: End of time range (optional)
            limit: Maximum number of snapshots

        Returns:
            List of StateSnapshots showing state evolution
        """
        # Get all events in range
        query = self.db.query(EventModel).filter(
            and_(
                EventModel.aggregate_type == aggregate_type,
                EventModel.aggregate_id == aggregate_id,
            )
        )

        if start_time:
            query = query.filter(EventModel.occurred_at >= start_time)
        if end_time:
            query = query.filter(EventModel.occurred_at <= end_time)

        events = query.order_by(EventModel.aggregate_version).limit(limit).all()

        if not events:
            return []

        # Build snapshots incrementally
        snapshots = []
        state = {}

        for i, event in enumerate(events):
            # Apply event to state
            state = self._apply_event(state, event)

            # Create snapshot
            snapshot = StateSnapshot(
                aggregate_id=aggregate_id,
                aggregate_type=aggregate_type,
                state=state.copy(),
                version=event.aggregate_version,
                timestamp=event.occurred_at,
                event_count=i + 1,
            )
            snapshots.append(snapshot)

        return snapshots

    def compare_states(
        self,
        aggregate_type: str,
        aggregate_id: str,
        time_point_1: TimePoint,
        time_point_2: TimePoint,
    ) -> Dict[str, Any]:
        """Compare entity state between two points in time.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            time_point_1: First time point
            time_point_2: Second time point

        Returns:
            Dictionary with differences between states
        """
        snapshot_1 = self.get_state_at(aggregate_type, aggregate_id, time_point_1)
        snapshot_2 = self.get_state_at(aggregate_type, aggregate_id, time_point_2)

        if not snapshot_1 or not snapshot_2:
            return {
                "error": "Could not retrieve state at one or both time points",
                "snapshot_1": snapshot_1 is not None,
                "snapshot_2": snapshot_2 is not None,
            }

        # Calculate differences
        differences = self._calculate_diff(snapshot_1.state, snapshot_2.state)

        return {
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "time_point_1": {
                "version": snapshot_1.version,
                "timestamp": snapshot_1.timestamp.isoformat(),
            },
            "time_point_2": {
                "version": snapshot_2.version,
                "timestamp": snapshot_2.timestamp.isoformat(),
            },
            "differences": differences,
            "changed_fields": list(differences.keys()),
        }

    def get_events_between(
        self,
        aggregate_type: str,
        aggregate_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> List[EventModel]:
        """Get all events for an aggregate between two timestamps.

        Args:
            aggregate_type: Type of aggregate
            aggregate_id: Aggregate identifier
            start_time: Start timestamp
            end_time: End timestamp

        Returns:
            List of events in time range
        """
        return (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                    EventModel.occurred_at >= start_time,
                    EventModel.occurred_at <= end_time,
                )
            )
            .order_by(EventModel.aggregate_version)
            .all()
        )

    def _get_events_until_timestamp(
        self, aggregate_type: str, aggregate_id: str, timestamp: datetime
    ) -> List[EventModel]:
        """Get events up to a timestamp."""
        return (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                    EventModel.occurred_at <= timestamp,
                )
            )
            .order_by(EventModel.aggregate_version)
            .all()
        )

    def _get_events_until_version(
        self, aggregate_type: str, aggregate_id: str, version: int
    ) -> List[EventModel]:
        """Get events up to a version."""
        return (
            self.db.query(EventModel)
            .filter(
                and_(
                    EventModel.aggregate_type == aggregate_type,
                    EventModel.aggregate_id == aggregate_id,
                    EventModel.aggregate_version <= version,
                )
            )
            .order_by(EventModel.aggregate_version)
            .all()
        )

    def _replay_events(self, events: List[EventModel]) -> Dict[str, Any]:
        """Replay events to reconstruct state."""
        state = {}

        for event in events:
            state = self._apply_event(state, event)

        return state

    def _apply_event(self, state: Dict[str, Any], event: EventModel) -> Dict[str, Any]:
        """Apply a single event to state.

        This is a simplified implementation. In production, you would
        have domain-specific event handlers for each event type.
        """
        # Copy current state
        new_state = state.copy()

        # Apply event data to state
        if event.data:
            # Simple merge strategy - just update fields from event data
            new_state.update(event.data)

        # Track metadata
        new_state["_last_event_type"] = event.event_type
        new_state["_last_event_version"] = event.aggregate_version
        new_state["_last_event_timestamp"] = event.occurred_at

        return new_state

    def _calculate_diff(
        self, state_1: Dict[str, Any], state_2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate differences between two states."""
        differences = {}

        # Find changed and removed fields
        all_keys = set(state_1.keys()) | set(state_2.keys())

        for key in all_keys:
            # Skip internal metadata fields
            if key.startswith("_"):
                continue

            val_1 = state_1.get(key)
            val_2 = state_2.get(key)

            if val_1 != val_2:
                differences[key] = {
                    "before": val_1,
                    "after": val_2,
                    "changed": val_1 is not None and val_2 is not None,
                    "added": val_1 is None and val_2 is not None,
                    "removed": val_1 is not None and val_2 is None,
                }

        return differences
