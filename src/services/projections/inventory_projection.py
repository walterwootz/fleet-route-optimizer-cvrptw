"""Inventory Projection - Read model for parts and stock."""

from typing import List
from .base import BaseProjection
from ...models.railfleet.events import Event as EventModel
from ...config import get_logger

logger = get_logger(__name__)


class InventoryProjection(BaseProjection):
    """Projection for Inventory aggregate.

    Handled Events:
    - PartCreatedEvent
    - PartUpdatedEvent
    - StockMoveCreatedEvent
    - StockLevelChangedEvent
    """

    def get_handled_event_types(self) -> List[str]:
        """Return event types handled by this projection."""
        return [
            "PartCreatedEvent",
            "PartUpdatedEvent",
            "StockMoveCreatedEvent",
            "StockLevelChangedEvent",
        ]

    def handle_event(self, event: EventModel) -> None:
        """Process inventory events."""
        logger.info(f"Processing {event.event_type} for {event.aggregate_id}")

    def reset(self) -> None:
        """Reset the inventory projection."""
        super().reset()
        logger.info("Inventory projection reset complete")
