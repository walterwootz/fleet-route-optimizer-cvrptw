"""LWW-Register (Last-Write-Wins Register) CRDT."""

from typing import Any, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from .base import BaseCRDT
from .vector_clock import VectorClock


@dataclass
class LWWValue:
    """Value with timestamp for LWW comparison."""
    value: Any
    timestamp: datetime
    device_id: str

    def __lt__(self, other: "LWWValue") -> bool:
        """Compare by timestamp, then device_id for determinism."""
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        return self.device_id < other.device_id


class LWWRegister(BaseCRDT[Any]):
    """Last-Write-Wins Register CRDT.

    A simple CRDT that stores a single value and resolves conflicts
    by keeping the value with the latest timestamp.

    If timestamps are equal, the device_id is used as a tiebreaker
    for deterministic resolution.

    Example:
        >>> reg1 = LWWRegister("device1")
        >>> reg1.set("value1")
        >>> reg2 = LWWRegister("device2")
        >>> reg2.set("value2")
        >>> reg1.merge(reg2)
        >>> reg1.get()  # Returns "value2" if reg2's timestamp is later
    """

    def __init__(self, device_id: str, value: Optional[Any] = None):
        """Initialize LWW Register.

        Args:
            device_id: Unique identifier for this device
            value: Initial value (optional)
        """
        super().__init__(device_id)
        self._lww_value: Optional[LWWValue] = None
        if value is not None:
            self.set(value)

    def set(self, value: Any, timestamp: Optional[datetime] = None) -> "LWWRegister":
        """Set the value.

        Args:
            value: The value to set
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Self for method chaining
        """
        if timestamp is None:
            timestamp = datetime.utcnow()

        self._lww_value = LWWValue(
            value=value,
            timestamp=timestamp,
            device_id=self.device_id
        )

        # Increment vector clock
        self.clock.increment()

        return self

    def get(self) -> Optional[Any]:
        """Get the current value.

        Returns:
            The current value, or None if not set
        """
        if self._lww_value is None:
            return None
        return self._lww_value.value

    def merge(self, other: "LWWRegister") -> "LWWRegister":
        """Merge another LWW Register into this one.

        Keeps the value with the latest timestamp.

        Args:
            other: The other register to merge

        Returns:
            Self for method chaining
        """
        # Merge vector clocks
        self._merge_clocks(other)

        # Compare values and keep the latest
        if other._lww_value is not None:
            if self._lww_value is None:
                self._lww_value = LWWValue(
                    value=other._lww_value.value,
                    timestamp=other._lww_value.timestamp,
                    device_id=other._lww_value.device_id
                )
            elif other._lww_value.timestamp > self._lww_value.timestamp:
                # Other value is newer
                self._lww_value = LWWValue(
                    value=other._lww_value.value,
                    timestamp=other._lww_value.timestamp,
                    device_id=other._lww_value.device_id
                )
            elif (other._lww_value.timestamp == self._lww_value.timestamp and
                  other._lww_value.device_id > self._lww_value.device_id):
                # Same timestamp, use device_id as tiebreaker
                self._lww_value = LWWValue(
                    value=other._lww_value.value,
                    timestamp=other._lww_value.timestamp,
                    device_id=other._lww_value.device_id
                )

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "device_id": self.device_id,
            "clock": self.clock.to_dict(),
            "value": {
                "value": self._lww_value.value if self._lww_value else None,
                "timestamp": self._lww_value.timestamp.isoformat() if self._lww_value else None,
                "device_id": self._lww_value.device_id if self._lww_value else None,
            } if self._lww_value else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LWWRegister":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New LWWRegister instance
        """
        register = cls(device_id=data["device_id"])
        register.clock = VectorClock.from_dict(data["clock"])

        if data.get("value"):
            value_data = data["value"]
            if value_data["timestamp"]:
                register._lww_value = LWWValue(
                    value=value_data["value"],
                    timestamp=datetime.fromisoformat(value_data["timestamp"]),
                    device_id=value_data["device_id"]
                )

        return register

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"LWWRegister(device={self.device_id}, value={self.get()}, clock={self.clock})"
