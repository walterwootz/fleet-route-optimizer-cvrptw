"""CRDT (Conflict-Free Replicated Data Types) Infrastructure."""

from .vector_clock import VectorClock
from .base import BaseCRDT, CRDTType
from .lww_register import LWWRegister
from .or_set import ORSet
from .counter import GCounter, PNCounter
from .entity_crdt import VehicleCRDT, WorkOrderCRDT, StockMoveCRDT

__all__ = [
    # Core
    "VectorClock",
    "BaseCRDT",
    "CRDTType",
    # Types
    "LWWRegister",
    "ORSet",
    "GCounter",
    "PNCounter",
    # Entity Wrappers
    "VehicleCRDT",
    "WorkOrderCRDT",
    "StockMoveCRDT",
]
