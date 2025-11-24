"""Procurement Projection - Read model for suppliers and purchase orders."""

from typing import List
from .base import BaseProjection
from ...models.railfleet.events import Event as EventModel
from ...config import get_logger

logger = get_logger(__name__)


class ProcurementProjection(BaseProjection):
    """Projection for Procurement aggregate.

    Handled Events:
    - SupplierCreatedEvent
    - PurchaseOrderCreatedEvent
    - PurchaseOrderApprovedEvent
    - PurchaseOrderReceivedEvent
    """

    def get_handled_event_types(self) -> List[str]:
        """Return event types handled by this projection."""
        return [
            "SupplierCreatedEvent",
            "PurchaseOrderCreatedEvent",
            "PurchaseOrderApprovedEvent",
            "PurchaseOrderReceivedEvent",
        ]

    def handle_event(self, event: EventModel) -> None:
        """Process procurement events."""
        logger.info(f"Processing {event.event_type} for {event.aggregate_id}")

    def reset(self) -> None:
        """Reset the procurement projection."""
        super().reset()
        logger.info("Procurement projection reset complete")
