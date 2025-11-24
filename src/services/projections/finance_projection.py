"""Finance Projection - Read model for invoices and budgets."""

from typing import List
from .base import BaseProjection
from ...models.railfleet.events import Event as EventModel
from ...config import get_logger

logger = get_logger(__name__)


class FinanceProjection(BaseProjection):
    """Projection for Finance aggregate.

    Handled Events:
    - InvoiceCreatedEvent
    - InvoiceApprovedEvent
    - BudgetUpdatedEvent
    """

    def get_handled_event_types(self) -> List[str]:
        """Return event types handled by this projection."""
        return [
            "InvoiceCreatedEvent",
            "InvoiceApprovedEvent",
            "BudgetUpdatedEvent",
        ]

    def handle_event(self, event: EventModel) -> None:
        """Process finance events."""
        logger.info(f"Processing {event.event_type} for {event.aggregate_id}")

    def reset(self) -> None:
        """Reset the finance projection."""
        super().reset()
        logger.info("Finance projection reset complete")
