"""Projection services for Event Sourcing."""

from .base import BaseProjection, ProjectionManager
from .vehicle_projection import VehicleProjection
from .maintenance_projection import MaintenanceProjection
from .inventory_projection import InventoryProjection
from .procurement_projection import ProcurementProjection
from .finance_projection import FinanceProjection

__all__ = [
    "BaseProjection",
    "ProjectionManager",
    "VehicleProjection",
    "MaintenanceProjection",
    "InventoryProjection",
    "ProcurementProjection",
    "FinanceProjection",
]
