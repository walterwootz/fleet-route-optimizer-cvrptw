"""
RailFleet database models.
"""
from .user import User
from .vehicle import Vehicle, VehicleStatus, VehicleType
from .maintenance import (
    MaintenanceTask,
    WorkOrder,
    SyncConflict,
    MaintenanceType,
    WorkOrderStatus,
    WorkOrderPriority,
)
from .workshop import Workshop

__all__ = [
    "User",
    "Vehicle",
    "VehicleStatus",
    "VehicleType",
    "MaintenanceTask",
    "WorkOrder",
    "SyncConflict",
    "MaintenanceType",
    "WorkOrderStatus",
    "WorkOrderPriority",
    "Workshop",
]
