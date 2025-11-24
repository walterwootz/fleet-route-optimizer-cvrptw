"""Event Sourcing Models - Base classes and event types."""

from .base import BaseEvent, EventMetadata, AggregateRoot
from .vehicle_events import (
    VehicleCreatedEvent,
    VehicleUpdatedEvent,
    VehicleDeletedEvent,
    VehicleStatusChangedEvent,
    VehicleMileageUpdatedEvent,
)
from .maintenance_events import (
    MaintenanceTaskCreatedEvent,
    WorkOrderCreatedEvent,
    WorkOrderStatusChangedEvent,
    WorkOrderCompletedEvent,
)
from .inventory_events import (
    PartCreatedEvent,
    PartUpdatedEvent,
    StockMoveCreatedEvent,
    StockLevelChangedEvent,
)
from .procurement_events import (
    SupplierCreatedEvent,
    PurchaseOrderCreatedEvent,
    PurchaseOrderApprovedEvent,
    PurchaseOrderReceivedEvent,
)
from .finance_events import (
    InvoiceCreatedEvent,
    InvoiceApprovedEvent,
    BudgetUpdatedEvent,
)

__all__ = [
    # Base
    "BaseEvent",
    "EventMetadata",
    "AggregateRoot",
    # Vehicle
    "VehicleCreatedEvent",
    "VehicleUpdatedEvent",
    "VehicleDeletedEvent",
    "VehicleStatusChangedEvent",
    "VehicleMileageUpdatedEvent",
    # Maintenance
    "MaintenanceTaskCreatedEvent",
    "WorkOrderCreatedEvent",
    "WorkOrderStatusChangedEvent",
    "WorkOrderCompletedEvent",
    # Inventory
    "PartCreatedEvent",
    "PartUpdatedEvent",
    "StockMoveCreatedEvent",
    "StockLevelChangedEvent",
    # Procurement
    "SupplierCreatedEvent",
    "PurchaseOrderCreatedEvent",
    "PurchaseOrderApprovedEvent",
    "PurchaseOrderReceivedEvent",
    # Finance
    "InvoiceCreatedEvent",
    "InvoiceApprovedEvent",
    "BudgetUpdatedEvent",
]
