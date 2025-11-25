"""Base CRDT classes and types."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar
from enum import Enum
from dataclasses import dataclass
from .vector_clock import VectorClock


class CRDTType(Enum):
    """Types of CRDTs."""
    LWW_REGISTER = "lww_register"      # Last-Write-Wins Register
    OR_SET = "or_set"                   # Observed-Remove Set
    G_COUNTER = "g_counter"             # Grow-only Counter
    PN_COUNTER = "pn_counter"           # Positive-Negative Counter
    LWW_MAP = "lww_map"                 # Last-Write-Wins Map


T = TypeVar('T')


@dataclass
class CRDTMetadata:
    """Metadata for CRDT operations."""
    device_id: str
    vector_clock: VectorClock
    tombstone: bool = False  # For deletion tracking

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "device_id": self.device_id,
            "vector_clock": self.vector_clock.to_dict(),
            "tombstone": self.tombstone
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CRDTMetadata":
        """Create from dictionary."""
        return cls(
            device_id=data["device_id"],
            vector_clock=VectorClock.from_dict(data["vector_clock"]),
            tombstone=data.get("tombstone", False)
        )


class BaseCRDT(ABC, Generic[T]):
    """Base class for all CRDTs.

    CRDTs (Conflict-Free Replicated Data Types) are data structures that
    can be replicated across multiple devices and merged without conflicts.

    Key properties:
    - Convergence: All replicas eventually converge to the same state
    - Commutativity: Merge order doesn't matter (A + B = B + A)
    - Associativity: Grouping doesn't matter ((A + B) + C = A + (B + C))
    - Idempotency: Merging with same state is safe (A + A = A)
    """

    def __init__(self, device_id: str):
        """Initialize CRDT.

        Args:
            device_id: Unique identifier for this device/replica
        """
        self.device_id = device_id
        self.clock = VectorClock(device_id=device_id)

    @abstractmethod
    def merge(self, other: "BaseCRDT[T]") -> "BaseCRDT[T]":
        """Merge another CRDT into this one.

        This operation must be:
        - Commutative: merge(A, B) = merge(B, A)
        - Associative: merge(merge(A, B), C) = merge(A, merge(B, C))
        - Idempotent: merge(A, A) = A

        Args:
            other: The other CRDT to merge

        Returns:
            Self for method chaining
        """
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert CRDT to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseCRDT[T]":
        """Create CRDT from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New CRDT instance
        """
        pass

    def _merge_clocks(self, other: "BaseCRDT[T]") -> None:
        """Merge vector clocks.

        Args:
            other: The other CRDT
        """
        self.clock.merge(other.clock)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(device={self.device_id}, clock={self.clock})"


class CRDTOperation:
    """Represents a CRDT operation for transmission/storage."""

    def __init__(
        self,
        crdt_type: CRDTType,
        operation: str,
        data: Dict[str, Any],
        metadata: CRDTMetadata
    ):
        """Initialize CRDT operation.

        Args:
            crdt_type: Type of CRDT
            operation: Operation name (e.g., 'set', 'add', 'remove')
            data: Operation data
            metadata: CRDT metadata
        """
        self.crdt_type = crdt_type
        self.operation = operation
        self.data = data
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "crdt_type": self.crdt_type.value,
            "operation": self.operation,
            "data": self.data,
            "metadata": self.metadata.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CRDTOperation":
        """Create from dictionary."""
        return cls(
            crdt_type=CRDTType(data["crdt_type"]),
            operation=data["operation"],
            data=data["data"],
            metadata=CRDTMetadata.from_dict(data["metadata"])
        )
