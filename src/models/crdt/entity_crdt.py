"""Entity CRDT Wrappers for domain models."""

from typing import Dict, Any, Optional
from datetime import datetime
from .lww_register import LWWRegister
from .or_set import ORSet
from .counter import PNCounter
from .vector_clock import VectorClock


class VehicleCRDT:
    """CRDT wrapper for Vehicle entity.

    Uses LWW-Registers for most fields that can be updated independently.
    """

    def __init__(self, device_id: str, asset_id: str):
        """Initialize Vehicle CRDT.

        Args:
            device_id: Unique device identifier
            asset_id: Vehicle asset ID
        """
        self.device_id = device_id
        self.asset_id = asset_id
        self.clock = VectorClock(device_id=device_id)

        # LWW Registers for individual fields
        self.status = LWWRegister(device_id)
        self.current_mileage = LWWRegister(device_id)
        self.model = LWWRegister(device_id)
        self.manufacturer = LWWRegister(device_id)
        self.location = LWWRegister(device_id)

    def update_status(self, status: str, timestamp: Optional[datetime] = None) -> "VehicleCRDT":
        """Update vehicle status.

        Args:
            status: New status value
            timestamp: Optional timestamp

        Returns:
            Self for method chaining
        """
        self.status.set(status, timestamp)
        self.clock.increment()
        return self

    def update_mileage(self, mileage: int, timestamp: Optional[datetime] = None) -> "VehicleCRDT":
        """Update vehicle mileage.

        Args:
            mileage: New mileage value
            timestamp: Optional timestamp

        Returns:
            Self for method chaining
        """
        self.current_mileage.set(mileage, timestamp)
        self.clock.increment()
        return self

    def merge(self, other: "VehicleCRDT") -> "VehicleCRDT":
        """Merge another Vehicle CRDT.

        Args:
            other: The other vehicle CRDT

        Returns:
            Self for method chaining
        """
        # Merge vector clock
        self.clock.merge(other.clock)

        # Merge all registers
        self.status.merge(other.status)
        self.current_mileage.merge(other.current_mileage)
        self.model.merge(other.model)
        self.manufacturer.merge(other.manufacturer)
        self.location.merge(other.location)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "device_id": self.device_id,
            "asset_id": self.asset_id,
            "clock": self.clock.to_dict(),
            "status": self.status.to_dict(),
            "current_mileage": self.current_mileage.to_dict(),
            "model": self.model.to_dict(),
            "manufacturer": self.manufacturer.to_dict(),
            "location": self.location.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VehicleCRDT":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New VehicleCRDT instance
        """
        vehicle = cls(
            device_id=data["device_id"],
            asset_id=data["asset_id"]
        )
        vehicle.clock = VectorClock.from_dict(data["clock"])
        vehicle.status = LWWRegister.from_dict(data["status"])
        vehicle.current_mileage = LWWRegister.from_dict(data["current_mileage"])
        vehicle.model = LWWRegister.from_dict(data["model"])
        vehicle.manufacturer = LWWRegister.from_dict(data["manufacturer"])
        vehicle.location = LWWRegister.from_dict(data["location"])
        return vehicle


class WorkOrderCRDT:
    """CRDT wrapper for WorkOrder entity.

    Uses LWW-Registers for status and timestamps.
    Uses OR-Set for tasks (can add/remove tasks).
    """

    def __init__(self, device_id: str, work_order_id: str):
        """Initialize WorkOrder CRDT.

        Args:
            device_id: Unique device identifier
            work_order_id: Work order ID
        """
        self.device_id = device_id
        self.work_order_id = work_order_id
        self.clock = VectorClock(device_id=device_id)

        # LWW Registers
        self.status = LWWRegister(device_id)
        self.priority = LWWRegister(device_id)
        self.actual_start = LWWRegister(device_id)
        self.actual_end = LWWRegister(device_id)

        # OR-Set for tasks (workshop can add findings)
        self.tasks = ORSet(device_id)

    def update_status(self, status: str, timestamp: Optional[datetime] = None) -> "WorkOrderCRDT":
        """Update work order status.

        Args:
            status: New status
            timestamp: Optional timestamp

        Returns:
            Self for method chaining
        """
        self.status.set(status, timestamp)
        self.clock.increment()
        return self

    def add_task(self, task: str) -> "WorkOrderCRDT":
        """Add a task to the work order.

        Args:
            task: Task description

        Returns:
            Self for method chaining
        """
        self.tasks.add(task)
        self.clock.increment()
        return self

    def merge(self, other: "WorkOrderCRDT") -> "WorkOrderCRDT":
        """Merge another WorkOrder CRDT.

        Args:
            other: The other work order CRDT

        Returns:
            Self for method chaining
        """
        # Merge vector clock
        self.clock.merge(other.clock)

        # Merge registers
        self.status.merge(other.status)
        self.priority.merge(other.priority)
        self.actual_start.merge(other.actual_start)
        self.actual_end.merge(other.actual_end)

        # Merge tasks set
        self.tasks.merge(other.tasks)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "device_id": self.device_id,
            "work_order_id": self.work_order_id,
            "clock": self.clock.to_dict(),
            "status": self.status.to_dict(),
            "priority": self.priority.to_dict(),
            "actual_start": self.actual_start.to_dict(),
            "actual_end": self.actual_end.to_dict(),
            "tasks": self.tasks.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkOrderCRDT":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New WorkOrderCRDT instance
        """
        work_order = cls(
            device_id=data["device_id"],
            work_order_id=data["work_order_id"]
        )
        work_order.clock = VectorClock.from_dict(data["clock"])
        work_order.status = LWWRegister.from_dict(data["status"])
        work_order.priority = LWWRegister.from_dict(data["priority"])
        work_order.actual_start = LWWRegister.from_dict(data["actual_start"])
        work_order.actual_end = LWWRegister.from_dict(data["actual_end"])
        work_order.tasks = ORSet.from_dict(data["tasks"])
        return work_order


class StockMoveCRDT:
    """CRDT wrapper for StockMove entity.

    Uses PNCounter for quantity changes.
    Uses LWW-Register for metadata.
    """

    def __init__(self, device_id: str, stock_move_id: str):
        """Initialize StockMove CRDT.

        Args:
            device_id: Unique device identifier
            stock_move_id: Stock move ID
        """
        self.device_id = device_id
        self.stock_move_id = stock_move_id
        self.clock = VectorClock(device_id=device_id)

        # PN Counter for quantity
        self.quantity = PNCounter(device_id)

        # LWW Registers
        self.move_type = LWWRegister(device_id)
        self.part_no = LWWRegister(device_id)
        self.location_id = LWWRegister(device_id)

    def adjust_quantity(self, amount: int) -> "StockMoveCRDT":
        """Adjust quantity.

        Args:
            amount: Amount to adjust (positive or negative)

        Returns:
            Self for method chaining
        """
        if amount > 0:
            self.quantity.increment(amount)
        elif amount < 0:
            self.quantity.decrement(abs(amount))

        self.clock.increment()
        return self

    def merge(self, other: "StockMoveCRDT") -> "StockMoveCRDT":
        """Merge another StockMove CRDT.

        Args:
            other: The other stock move CRDT

        Returns:
            Self for method chaining
        """
        # Merge vector clock
        self.clock.merge(other.clock)

        # Merge counter
        self.quantity.merge(other.quantity)

        # Merge registers
        self.move_type.merge(other.move_type)
        self.part_no.merge(other.part_no)
        self.location_id.merge(other.location_id)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "device_id": self.device_id,
            "stock_move_id": self.stock_move_id,
            "clock": self.clock.to_dict(),
            "quantity": self.quantity.to_dict(),
            "move_type": self.move_type.to_dict(),
            "part_no": self.part_no.to_dict(),
            "location_id": self.location_id.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StockMoveCRDT":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New StockMoveCRDT instance
        """
        stock_move = cls(
            device_id=data["device_id"],
            stock_move_id=data["stock_move_id"]
        )
        stock_move.clock = VectorClock.from_dict(data["clock"])
        stock_move.quantity = PNCounter.from_dict(data["quantity"])
        stock_move.move_type = LWWRegister.from_dict(data["move_type"])
        stock_move.part_no = LWWRegister.from_dict(data["part_no"])
        stock_move.location_id = LWWRegister.from_dict(data["location_id"])
        return stock_move
