"""Maintenance Domain Events."""

from .base import BaseEvent


class MaintenanceTaskCreatedEvent(BaseEvent):
    """Event raised when a maintenance task is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'MaintenanceTask'
        super().__init__(**data)


class WorkOrderCreatedEvent(BaseEvent):
    """Event raised when a work order is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'WorkOrder'
        super().__init__(**data)


class WorkOrderStatusChangedEvent(BaseEvent):
    """Event raised when a work order status changes."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'WorkOrder'
        super().__init__(**data)


class WorkOrderCompletedEvent(BaseEvent):
    """Event raised when a work order is completed."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'WorkOrder'
        super().__init__(**data)
