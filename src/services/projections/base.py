"""Base Projection classes for Event Sourcing."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Type, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ...models.events.base import BaseEvent
from ...models.railfleet.events import Event as EventModel
from ...services.event_store import EventStore
from ...config import get_logger

logger = get_logger(__name__)


class BaseProjection(ABC):
    """Base class for event projections.

    Projections are read models that are built from events.
    They provide optimized views of the data for querying.

    Each projection:
    - Subscribes to specific event types
    - Processes events to update its state
    - Can be rebuilt from event history
    - Tracks the last processed event version
    """

    def __init__(self, db: Session):
        self.db = db
        self.name = self.__class__.__name__
        self._last_processed_version: Dict[str, int] = {}

    @abstractmethod
    def get_handled_event_types(self) -> List[str]:
        """Return list of event types this projection handles.

        Returns:
            List of event type names (e.g., ['VehicleCreatedEvent', 'VehicleUpdatedEvent'])
        """
        pass

    @abstractmethod
    def handle_event(self, event: EventModel) -> None:
        """Process an event and update the projection.

        Args:
            event: The event to process
        """
        pass

    def can_handle(self, event: EventModel) -> bool:
        """Check if this projection can handle the given event.

        Args:
            event: The event to check

        Returns:
            True if this projection handles this event type
        """
        return event.event_type in self.get_handled_event_types()

    def process_event(self, event: EventModel) -> None:
        """Process an event if this projection handles it.

        This method:
        1. Checks if the event should be handled
        2. Calls the specific event handler
        3. Updates the last processed version
        4. Commits the transaction

        Args:
            event: The event to process
        """
        if not self.can_handle(event):
            return

        try:
            # Call the specific handler
            self.handle_event(event)

            # Update last processed version
            self._last_processed_version[event.aggregate_id] = event.aggregate_version

            # Commit the changes
            self.db.commit()

            logger.debug(
                f"{self.name}: Processed {event.event_type} for {event.aggregate_id} v{event.aggregate_version}"
            )

        except Exception as e:
            self.db.rollback()
            logger.error(
                f"{self.name}: Error processing {event.event_type} for {event.aggregate_id}: {e}",
                exc_info=True
            )
            raise

    def get_last_processed_version(self, aggregate_id: str) -> int:
        """Get the last processed version for an aggregate.

        Args:
            aggregate_id: The aggregate ID

        Returns:
            Last processed version, or 0 if not processed yet
        """
        return self._last_processed_version.get(aggregate_id, 0)

    def rebuild(self, aggregate_id: Optional[str] = None) -> None:
        """Rebuild the projection from event history.

        This is useful for:
        - Initial projection creation
        - Fixing projection bugs
        - Adding new projections to existing systems

        Args:
            aggregate_id: Rebuild for specific aggregate, or None for all
        """
        event_store = EventStore(self.db)

        if aggregate_id:
            # Rebuild for specific aggregate
            events = event_store.get_events(aggregate_id)
            logger.info(f"{self.name}: Rebuilding projection for {aggregate_id} ({len(events)} events)")

            for event in events:
                if self.can_handle(event):
                    self.process_event(event)
        else:
            # Rebuild for all aggregates
            # Get all events that this projection handles
            for event_type in self.get_handled_event_types():
                events = event_store.get_all_events(
                    event_type=event_type,
                    limit=10000  # Process in batches
                )

                logger.info(f"{self.name}: Rebuilding projection for {event_type} ({len(events)} events)")

                for event in events:
                    self.process_event(event)

        logger.info(f"{self.name}: Rebuild complete")

    def reset(self) -> None:
        """Reset the projection (clear all data).

        This method should be implemented by subclasses to clear
        their specific projection data.
        """
        self._last_processed_version.clear()
        logger.info(f"{self.name}: Reset complete")


class ProjectionManager:
    """Manager for all projections.

    The ProjectionManager:
    - Registers projections
    - Routes events to appropriate projections
    - Rebuilds projections
    - Monitors projection health
    """

    def __init__(self, db: Session):
        self.db = db
        self._projections: List[BaseProjection] = []
        self._event_type_to_projections: Dict[str, List[BaseProjection]] = {}

    def register(self, projection: BaseProjection) -> None:
        """Register a projection.

        Args:
            projection: The projection to register
        """
        self._projections.append(projection)

        # Build event type index
        for event_type in projection.get_handled_event_types():
            if event_type not in self._event_type_to_projections:
                self._event_type_to_projections[event_type] = []
            self._event_type_to_projections[event_type].append(projection)

        logger.info(f"Registered projection: {projection.name}")

    def process_event(self, event: EventModel) -> None:
        """Process an event through all relevant projections.

        Args:
            event: The event to process
        """
        # Get projections that handle this event type
        projections = self._event_type_to_projections.get(event.event_type, [])

        for projection in projections:
            try:
                projection.process_event(event)
            except Exception as e:
                logger.error(
                    f"Error processing event {event.event_id} in {projection.name}: {e}",
                    exc_info=True
                )
                # Continue processing other projections

    def rebuild_all(self) -> None:
        """Rebuild all registered projections from event history."""
        logger.info(f"Rebuilding {len(self._projections)} projections...")

        for projection in self._projections:
            try:
                projection.rebuild()
            except Exception as e:
                logger.error(f"Error rebuilding {projection.name}: {e}", exc_info=True)

        logger.info("All projections rebuilt")

    def rebuild_projection(self, projection_name: str, aggregate_id: Optional[str] = None) -> None:
        """Rebuild a specific projection.

        Args:
            projection_name: Name of the projection to rebuild
            aggregate_id: Optional aggregate ID to rebuild for

        Raises:
            ValueError: If projection not found
        """
        projection = next(
            (p for p in self._projections if p.name == projection_name),
            None
        )

        if not projection:
            raise ValueError(f"Projection {projection_name} not found")

        logger.info(f"Rebuilding projection: {projection_name}")
        projection.rebuild(aggregate_id)

    def get_projection_stats(self) -> Dict[str, Any]:
        """Get statistics about registered projections.

        Returns:
            Dictionary with projection statistics
        """
        stats = {
            "total_projections": len(self._projections),
            "projections": []
        }

        for projection in self._projections:
            proj_stats = {
                "name": projection.name,
                "handled_event_types": projection.get_handled_event_types(),
                "handled_events_count": len(projection.get_handled_event_types())
            }
            stats["projections"].append(proj_stats)

        return stats


# Global projection manager instance
_projection_manager: Optional[ProjectionManager] = None


def get_projection_manager(db: Session) -> ProjectionManager:
    """Get the global projection manager instance.

    Args:
        db: Database session

    Returns:
        The projection manager
    """
    global _projection_manager
    if _projection_manager is None:
        _projection_manager = ProjectionManager(db)
    return _projection_manager


def reset_projection_manager() -> None:
    """Reset the global projection manager (useful for testing)."""
    global _projection_manager
    _projection_manager = None
