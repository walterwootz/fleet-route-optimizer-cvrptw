"""Counter CRDTs (GCounter and PNCounter)."""

from typing import Dict, Any
from .base import BaseCRDT
from .vector_clock import VectorClock


class GCounter(BaseCRDT[int]):
    """Grow-only Counter CRDT.

    A counter that can only be incremented (monotonically increasing).
    Each device maintains its own counter, and the global value is the sum.

    Example:
        >>> counter1 = GCounter("device1")
        >>> counter1.increment(5)
        >>> counter2 = GCounter("device2")
        >>> counter2.increment(3)
        >>> counter1.merge(counter2)
        >>> counter1.value()  # 8
    """

    def __init__(self, device_id: str):
        """Initialize GCounter.

        Args:
            device_id: Unique identifier for this device
        """
        super().__init__(device_id)
        # Dictionary: device_id -> counter value
        self._counters: Dict[str, int] = {device_id: 0}

    def increment(self, amount: int = 1) -> "GCounter":
        """Increment this device's counter.

        Args:
            amount: Amount to increment by (must be >= 0)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If amount is negative
        """
        if amount < 0:
            raise ValueError("GCounter can only increment (amount must be >= 0)")

        self._counters[self.device_id] = self._counters.get(self.device_id, 0) + amount

        # Increment vector clock
        self.clock.increment()

        return self

    def value(self) -> int:
        """Get the current counter value (sum of all device counters).

        Returns:
            The current value
        """
        return sum(self._counters.values())

    def merge(self, other: "GCounter") -> "GCounter":
        """Merge another GCounter into this one.

        Takes the maximum value for each device.

        Args:
            other: The other counter to merge

        Returns:
            Self for method chaining
        """
        # Merge vector clocks
        self._merge_clocks(other)

        # Merge counters (take maximum for each device)
        for device_id, count in other._counters.items():
            self._counters[device_id] = max(
                self._counters.get(device_id, 0),
                count
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
            "counters": self._counters
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GCounter":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New GCounter instance
        """
        counter = cls(device_id=data["device_id"])
        counter.clock = VectorClock.from_dict(data["clock"])
        counter._counters = data.get("counters", {data["device_id"]: 0})
        return counter

    def __int__(self) -> int:
        """Get the counter value as int."""
        return self.value()

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"GCounter(device={self.device_id}, value={self.value()}, clock={self.clock})"


class PNCounter(BaseCRDT[int]):
    """Positive-Negative Counter CRDT.

    A counter that can be both incremented and decremented.
    Implemented using two GCounters (one for increments, one for decrements).

    Example:
        >>> counter1 = PNCounter("device1")
        >>> counter1.increment(10)
        >>> counter1.decrement(3)
        >>> counter1.value()  # 7
    """

    def __init__(self, device_id: str):
        """Initialize PNCounter.

        Args:
            device_id: Unique identifier for this device
        """
        super().__init__(device_id)
        self._increments = GCounter(device_id)
        self._decrements = GCounter(device_id)

    def increment(self, amount: int = 1) -> "PNCounter":
        """Increment the counter.

        Args:
            amount: Amount to increment by (must be >= 0)

        Returns:
            Self for method chaining
        """
        self._increments.increment(amount)

        # Increment vector clock
        self.clock.increment()

        return self

    def decrement(self, amount: int = 1) -> "PNCounter":
        """Decrement the counter.

        Args:
            amount: Amount to decrement by (must be >= 0)

        Returns:
            Self for method chaining
        """
        self._decrements.increment(amount)

        # Increment vector clock
        self.clock.increment()

        return self

    def value(self) -> int:
        """Get the current counter value (increments - decrements).

        Returns:
            The current value
        """
        return self._increments.value() - self._decrements.value()

    def merge(self, other: "PNCounter") -> "PNCounter":
        """Merge another PNCounter into this one.

        Args:
            other: The other counter to merge

        Returns:
            Self for method chaining
        """
        # Merge vector clocks
        self._merge_clocks(other)

        # Merge both GCounters
        self._increments.merge(other._increments)
        self._decrements.merge(other._decrements)

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "device_id": self.device_id,
            "clock": self.clock.to_dict(),
            "increments": self._increments.to_dict(),
            "decrements": self._decrements.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PNCounter":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New PNCounter instance
        """
        counter = cls(device_id=data["device_id"])
        counter.clock = VectorClock.from_dict(data["clock"])
        counter._increments = GCounter.from_dict(data["increments"])
        counter._decrements = GCounter.from_dict(data["decrements"])
        return counter

    def __int__(self) -> int:
        """Get the counter value as int."""
        return self.value()

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"PNCounter(device={self.device_id}, value={self.value()}, clock={self.clock})"
