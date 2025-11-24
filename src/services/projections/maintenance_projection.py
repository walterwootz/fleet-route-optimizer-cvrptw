"""Maintenance Projection - Read model for maintenance tasks and work orders."""

from typing import List
from sqlalchemy.orm import Session

from .base import BaseProjection
from ...models.railfleet.events import Event as EventModel
from ...models.railfleet.maintenance import WorkOrder, WorkOrderStatus
from ...config import get_logger

logger = get_logger(__name__)


class MaintenanceProjection(BaseProjection):
    """Projection for Maintenance aggregate.

    Handled Events:
    - MaintenanceTaskCreatedEvent
    - WorkOrderCreatedEvent
    - WorkOrderStatusChangedEvent
    - WorkOrderCompletedEvent
    """

    def get_handled_event_types(self) -> List[str]:
        """Return event types handled by this projection."""
        return [
            "MaintenanceTaskCreatedEvent",
            "WorkOrderCreatedEvent",
            "WorkOrderStatusChangedEvent",
            "WorkOrderCompletedEvent",
        ]

    def handle_event(self, event: EventModel) -> None:
        """Process maintenance events.

        Args:
            event: The event to process
        """
        handler_map = {
            "WorkOrderCreatedEvent": self._handle_work_order_created,
            "WorkOrderStatusChangedEvent": self._handle_status_changed,
            "WorkOrderCompletedEvent": self._handle_work_order_completed,
        }

        handler = handler_map.get(event.event_type)
        if handler:
            handler(event)

    def _handle_work_order_created(self, event: EventModel) -> None:
        """Handle WorkOrderCreatedEvent."""
        # Implementation would create/update work order
        logger.info(f"Processing WorkOrderCreatedEvent for {event.aggregate_id}")

    def _handle_status_changed(self, event: EventModel) -> None:
        """Handle WorkOrderStatusChangedEvent."""
        data = event.data
        logger.info(
            f"Work order {event.aggregate_id} status: {data.get('old_status')} → {data.get('new_status')}"
        )

    def _handle_work_order_completed(self, event: EventModel) -> None:
        """Handle WorkOrderCompletedEvent."""
        logger.info(f"Work order {event.aggregate_id} completed")

    def reset(self) -> None:
        """Reset the maintenance projection."""
        super().reset()
        logger.info("Maintenance projection reset complete")
