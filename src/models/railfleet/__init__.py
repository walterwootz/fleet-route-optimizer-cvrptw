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
from .transfer import TransferPlan, TransferAssignment, TransferStatus, TransferPriority
from .hr import Staff, StaffAssignment, StaffRole, StaffStatus
from .docs import DocumentLink, DocumentVersion, DocumentAccessLog, DocumentType, DocumentStatus
from .event_log import EventLog
from .inventory import Part, StockLocation, StockMove, UsedPart, RailwayClass, StockMoveType

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
    "TransferPlan",
    "TransferAssignment",
    "TransferStatus",
    "TransferPriority",
    "Staff",
    "StaffAssignment",
    "StaffRole",
    "StaffStatus",
    "DocumentLink",
    "DocumentVersion",
    "DocumentAccessLog",
    "DocumentType",
    "DocumentStatus",
    "EventLog",
    "Part",
    "StockLocation",
    "StockMove",
    "UsedPart",
    "RailwayClass",
    "StockMoveType",
]
