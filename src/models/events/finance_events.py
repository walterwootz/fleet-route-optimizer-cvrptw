"""Finance Domain Events."""

from .base import BaseEvent


class InvoiceCreatedEvent(BaseEvent):
    """Event raised when an invoice is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Invoice'
        super().__init__(**data)


class InvoiceApprovedEvent(BaseEvent):
    """Event raised when an invoice is approved."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Invoice'
        super().__init__(**data)


class BudgetUpdatedEvent(BaseEvent):
    """Event raised when budget is updated."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Budget'
        super().__init__(**data)
