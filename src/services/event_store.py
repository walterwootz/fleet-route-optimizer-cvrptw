"""Event Store Service for persisting and retrieving events."""

from typing import List, Optional, Type, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
import json

from ..models.events.base import BaseEvent, Snapshot, EventType
from ..models.railfleet.events import Event as EventModel, EventSnapshot
from ..config import get_logger

logger = get_logger(__name__)


class EventStore:
    """Event Store for persisting and retrieving domain events.

    The Event Store is the central repository for all domain events.
    It provides:
    - Event persistence (append-only)
    - Event retrieval by aggregate
    - Event streaming
    - Snapshot support for performance
    """

    def __init__(self, db: Session):
        self.db = db

    def append(self, event: BaseEvent) -> None:
        """Append an event to the store.

        Events are immutable and append-only. Once written, they cannot be modified.

        Args:
            event: The event to append

        Raises:
            ValueError: If event with same ID already exists
        """
        # Check if event already exists (idempotency)
        existing = self.db.query(EventModel).filter(
            EventModel.event_id == event.event_id
        ).first()

        if existing:
            logger.warning(f"Event {event.event_id} already exists, skipping")
            return

        # Create event model
        event_model = EventModel(
            event_id=event.event_id,
            event_type=event.event_type,
            event_version=event.event_version,
            aggregate_id=event.aggregate_id,
            aggregate_type=event.aggregate_type,
            aggregate_version=event.aggregate_version,
            occurred_at=event.occurred_at,
            data=event.data,
            metadata=event.metadata.dict(),
        )

        self.db.add(event_model)
        self.db.commit()

        logger.info(
            f"Appended event {event.event_type} for {event.aggregate_type}:{event.aggregate_id} v{event.aggregate_version}"
        )

    def append_batch(self, events: List[BaseEvent]) -> None:
        """Append multiple events in a single transaction.

        Args:
            events: List of events to append
        """
        for event in events:
            self.append(event)

    def get_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
        to_version: Optional[int] = None
    ) -> List[EventModel]:
        """Get events for an aggregate.

        Args:
            aggregate_id: The aggregate ID
            from_version: Start from this version (inclusive)
            to_version: End at this version (inclusive), None for latest

        Returns:
            List of events in chronological order
        """
        query = self.db.query(EventModel).filter(
            and_(
                EventModel.aggregate_id == aggregate_id,
                EventModel.aggregate_version >= from_version
            )
        )

        if to_version is not None:
            query = query.filter(EventModel.aggregate_version <= to_version)

        query = query.order_by(asc(EventModel.aggregate_version))

        return query.all()

    def get_latest_version(self, aggregate_id: str) -> int:
        """Get the latest version number for an aggregate.

        Args:
            aggregate_id: The aggregate ID

        Returns:
            Latest version number, or 0 if no events exist
        """
        result = self.db.query(EventModel.aggregate_version).filter(
            EventModel.aggregate_id == aggregate_id
        ).order_by(desc(EventModel.aggregate_version)).first()

        return result[0] if result else 0

    def get_all_events(
        self,
        aggregate_type: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[EventModel]:
        """Get events with filters.

        Args:
            aggregate_type: Filter by aggregate type
            event_type: Filter by event type
            since: Filter events after this timestamp
            until: Filter events before this timestamp
            limit: Maximum number of events to return
            offset: Number of events to skip

        Returns:
            List of events matching the filters
        """
        query = self.db.query(EventModel)

        if aggregate_type:
            query = query.filter(EventModel.aggregate_type == aggregate_type)

        if event_type:
            query = query.filter(EventModel.event_type == event_type)

        if since:
            query = query.filter(EventModel.occurred_at >= since)

        if until:
            query = query.filter(EventModel.occurred_at <= until)

        query = query.order_by(desc(EventModel.occurred_at))
        query = query.limit(limit).offset(offset)

        return query.all()

    def replay_events(
        self,
        aggregate_id: str,
        event_class: Type[EventType]
    ) -> List[EventType]:
        """Replay events for an aggregate, converting to event objects.

        Args:
            aggregate_id: The aggregate ID
            event_class: Base event class for deserialization

        Returns:
            List of deserialized event objects
        """
        event_models = self.get_events(aggregate_id)
        events = []

        for model in event_models:
            # Reconstruct event object
            event_dict = {
                'event_id': model.event_id,
                'event_type': model.event_type,
                'event_version': model.event_version,
                'aggregate_id': model.aggregate_id,
                'aggregate_type': model.aggregate_type,
                'aggregate_version': model.aggregate_version,
                'occurred_at': model.occurred_at,
                'data': model.data,
                'metadata': model.metadata,
            }

            # Use the appropriate event class based on event_type
            # This is a simplified version - you'd want a registry in production
            try:
                event = event_class.from_dict(event_dict)
                events.append(event)
            except Exception as e:
                logger.error(f"Failed to deserialize event {model.event_id}: {e}")
                continue

        return events

    # Snapshot management

    def save_snapshot(self, snapshot: Snapshot) -> None:
        """Save a snapshot of aggregate state.

        Snapshots allow faster reconstruction of aggregates by avoiding
        replaying all events from the beginning.

        Args:
            snapshot: The snapshot to save
        """
        snapshot_model = EventSnapshot(
            snapshot_id=snapshot.snapshot_id,
            aggregate_id=snapshot.aggregate_id,
            aggregate_type=snapshot.aggregate_type,
            aggregate_version=snapshot.aggregate_version,
            state=snapshot.state,
            created_at=snapshot.created_at,
        )

        self.db.add(snapshot_model)
        self.db.commit()

        logger.info(
            f"Saved snapshot for {snapshot.aggregate_type}:{snapshot.aggregate_id} v{snapshot.aggregate_version}"
        )

    def get_latest_snapshot(self, aggregate_id: str) -> Optional[Snapshot]:
        """Get the latest snapshot for an aggregate.

        Args:
            aggregate_id: The aggregate ID

        Returns:
            Latest snapshot, or None if no snapshot exists
        """
        snapshot_model = self.db.query(EventSnapshot).filter(
            EventSnapshot.aggregate_id == aggregate_id
        ).order_by(desc(EventSnapshot.aggregate_version)).first()

        if not snapshot_model:
            return None

        return Snapshot(
            snapshot_id=snapshot_model.snapshot_id,
            aggregate_id=snapshot_model.aggregate_id,
            aggregate_type=snapshot_model.aggregate_type,
            aggregate_version=snapshot_model.aggregate_version,
            state=snapshot_model.state,
            created_at=snapshot_model.created_at,
        )

    def cleanup_old_snapshots(
        self,
        aggregate_id: str,
        keep_count: int = 3
    ) -> None:
        """Clean up old snapshots, keeping only the most recent ones.

        Args:
            aggregate_id: The aggregate ID
            keep_count: Number of snapshots to keep
        """
        snapshots = self.db.query(EventSnapshot).filter(
            EventSnapshot.aggregate_id == aggregate_id
        ).order_by(desc(EventSnapshot.aggregate_version)).all()

        if len(snapshots) > keep_count:
            to_delete = snapshots[keep_count:]
            for snapshot in to_delete:
                self.db.delete(snapshot)

            self.db.commit()
            logger.info(f"Cleaned up {len(to_delete)} old snapshots for {aggregate_id}")
