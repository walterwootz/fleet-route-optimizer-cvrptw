"""Inventory Domain Events."""

from .base import BaseEvent


class PartCreatedEvent(BaseEvent):
    """Event raised when a part is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Part'
        super().__init__(**data)


class PartUpdatedEvent(BaseEvent):
    """Event raised when a part is updated."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Part'
        super().__init__(**data)


class StockMoveCreatedEvent(BaseEvent):
    """Event raised when a stock move is created."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'StockMove'
        super().__init__(**data)


class StockLevelChangedEvent(BaseEvent):
    """Event raised when stock level changes."""

    def __init__(self, **data):
        if 'aggregate_type' not in data:
            data['aggregate_type'] = 'Stock'
        super().__init__(**data)
