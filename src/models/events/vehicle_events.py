"""Vehicle Domain Events."""

from typing import Any, Dict, Optional
from .base import BaseEvent


class VehicleCreatedEvent(BaseEvent):
    """Event raised when a vehicle is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Vehicle'
        super().__init__(**data)


class VehicleUpdatedEvent(BaseEvent):
    """Event raised when a vehicle is updated."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Vehicle'
        super().__init__(**data)


class VehicleDeletedEvent(BaseEvent):
    """Event raised when a vehicle is deleted."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Vehicle'
        super().__init__(**data)


class VehicleStatusChangedEvent(BaseEvent):
    """Event raised when a vehicle status changes."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Vehicle'
        super().__init__(**data)


class VehicleMileageUpdatedEvent(BaseEvent):
    """Event raised when vehicle mileage is updated."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Vehicle'
        super().__init__(**data)
