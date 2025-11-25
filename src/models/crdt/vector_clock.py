"""Vector Clock for causality tracking in distributed systems."""

from typing import Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import json


class ClockRelation(Enum):
    """Relationship between two vector clocks."""
    EQUAL = "equal"              # Clocks are identical
    BEFORE = "before"            # This clock happened before other
    AFTER = "after"              # This clock happened after other
    CONCURRENT = "concurrent"    # Clocks are concurrent (conflict)


@dataclass
class VectorClock:
    """Vector Clock for tracking causality in distributed systems.

    A vector clock is a data structure used for determining the partial ordering
    of events in a distributed system and detecting causality violations.

    Each node in the system maintains a vector clock that maps node IDs to
    logical timestamps. When an event occurs, the node increments its own
    counter in the vector.

    Example:
        >>> clock1 = VectorClock(device_id="device1")
        >>> clock1.increment()
        >>> clock1.clocks
        {'device1': 1}

        >>> clock2 = VectorClock(device_id="device2")
        >>> clock2.increment()
        >>> clock2.merge(clock1)
        >>> clock2.clocks
        {'device1': 1, 'device2': 1}
    """

    device_id: str
    clocks: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize the clock for this device if not present."""
        if self.device_id not in self.clocks:
            self.clocks[self.device_id] = 0

    def increment(self) -> "VectorClock":
        """Increment this device's clock.

        Returns:
            Self for method chaining
        """
        self.clocks[self.device_id] = self.clocks.get(self.device_id, 0) + 1
        return self

    def merge(self, other: "VectorClock") -> "VectorClock":
        """Merge another vector clock into this one.

        Takes the maximum value for each device ID.

        Args:
            other: The other vector clock to merge

        Returns:
            Self for method chaining
        """
        # Get all device IDs from both clocks
        all_devices = set(self.clocks.keys()) | set(other.clocks.keys())

        # Take maximum for each device
        for device_id in all_devices:
            self_val = self.clocks.get(device_id, 0)
            other_val = other.clocks.get(device_id, 0)
            self.clocks[device_id] = max(self_val, other_val)

        return self

    def compare(self, other: "VectorClock") -> ClockRelation:
        """Compare this vector clock with another.

        Args:
            other: The other vector clock to compare

        Returns:
            The relationship between the two clocks
        """
        # Get all device IDs from both clocks
        all_devices = set(self.clocks.keys()) | set(other.clocks.keys())

        less_or_equal = True
        greater_or_equal = True

        for device_id in all_devices:
            self_val = self.clocks.get(device_id, 0)
            other_val = other.clocks.get(device_id, 0)

            if self_val > other_val:
                less_or_equal = False
            if self_val < other_val:
                greater_or_equal = False

        if less_or_equal and greater_or_equal:
            return ClockRelation.EQUAL
        elif less_or_equal:
            return ClockRelation.BEFORE
        elif greater_or_equal:
            return ClockRelation.AFTER
        else:
            return ClockRelation.CONCURRENT

    def is_concurrent(self, other: "VectorClock") -> bool:
        """Check if this clock is concurrent with another.

        Concurrent clocks indicate a potential conflict.

        Args:
            other: The other vector clock

        Returns:
            True if clocks are concurrent
        """
        return self.compare(other) == ClockRelation.CONCURRENT

    def happens_before(self, other: "VectorClock") -> bool:
        """Check if this clock happened before another.

        Args:
            other: The other vector clock

        Returns:
            True if this clock happened before other
        """
        return self.compare(other) == ClockRelation.BEFORE

    def happens_after(self, other: "VectorClock") -> bool:
        """Check if this clock happened after another.

        Args:
            other: The other vector clock

        Returns:
            True if this clock happened after other
        """
        return self.compare(other) == ClockRelation.AFTER

    def copy(self) -> "VectorClock":
        """Create a deep copy of this vector clock.

        Returns:
            A new VectorClock instance
        """
        return VectorClock(
            device_id=self.device_id,
            clocks=self.clocks.copy()
        )

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "device_id": self.device_id,
            "clocks": self.clocks
        }

    @classmethod
    def from_dict(cls, data: Dict[str, any]) -> "VectorClock":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New VectorClock instance
        """
        return cls(
            device_id=data["device_id"],
            clocks=data.get("clocks", {})
        )

    def to_json(self) -> str:
        """Convert to JSON string.

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "VectorClock":
        """Create from JSON string.

        Args:
            json_str: JSON string representation

        Returns:
            New VectorClock instance
        """
        return cls.from_dict(json.loads(json_str))

    def __str__(self) -> str:
        """String representation."""
        clock_str = ", ".join(f"{k}:{v}" for k, v in sorted(self.clocks.items()))
        return f"VectorClock({clock_str})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"VectorClock(device_id='{self.device_id}', clocks={self.clocks})"

    def __eq__(self, other: "VectorClock") -> bool:
        """Check equality."""
        if not isinstance(other, VectorClock):
            return False
        return self.compare(other) == ClockRelation.EQUAL

    def __lt__(self, other: "VectorClock") -> bool:
        """Check if this clock is before other."""
        return self.happens_before(other)

    def __gt__(self, other: "VectorClock") -> bool:
        """Check if this clock is after other."""
        return self.happens_after(other)
