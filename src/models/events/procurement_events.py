"""Procurement Domain Events."""

from .base import BaseEvent


class SupplierCreatedEvent(BaseEvent):
    """Event raised when a supplier is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Supplier'
        super().__init__(**data)


class PurchaseOrderCreatedEvent(BaseEvent):
    """Event raised when a purchase order is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'PurchaseOrder'
        super().__init__(**data)


class PurchaseOrderApprovedEvent(BaseEvent):
    """Event raised when a purchase order is approved."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'PurchaseOrder'
        super().__init__(**data)


class PurchaseOrderReceivedEvent(BaseEvent):
    """Event raised when a purchase order is received."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'PurchaseOrder'
        super().__init__(**data)
