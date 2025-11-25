"""OR-Set (Observed-Remove Set) CRDT."""

from typing import Any, Dict, Set, Tuple
from uuid import uuid4
from .base import BaseCRDT
from .vector_clock import VectorClock


class ORSet(BaseCRDT[Set[Any]]):
    """Observed-Remove Set CRDT.

    An OR-Set allows adding and removing elements from a set.
    It resolves conflicts by keeping elements that were added but not observed to be removed.

    Each element is tagged with a unique identifier to distinguish different add operations.
    An element is in the set if there exists an add tag that hasn't been removed.

    Example:
        >>> set1 = ORSet("device1")
        >>> set1.add("apple")
        >>> set1.add("banana")
        >>> set2 = ORSet("device2")
        >>> set2.add("orange")
        >>> set1.merge(set2)
        >>> set1.elements()  # {'apple', 'banana', 'orange'}
    """

    def __init__(self, device_id: str):
        """Initialize OR-Set.

        Args:
            device_id: Unique identifier for this device
        """
        super().__init__(device_id)
        # Dictionary: element -> set of (unique_id, device_id) tags
        self._elements: Dict[Any, Set[Tuple[str, str]]] = {}
        # Set of removed (element, unique_id, device_id) tuples
        self._tombstones: Set[Tuple[Any, str, str]] = set()

    def add(self, element: Any) -> "ORSet":
        """Add an element to the set.

        Args:
            element: The element to add

        Returns:
            Self for method chaining
        """
        # Generate unique tag for this add operation
        unique_id = str(uuid4())

        if element not in self._elements:
            self._elements[element] = set()

        self._elements[element].add((unique_id, self.device_id))

        # Increment vector clock
        self.clock.increment()

        return self

    def remove(self, element: Any) -> "ORSet":
        """Remove an element from the set.

        This observes all current add tags and marks them for removal.

        Args:
            element: The element to remove

        Returns:
            Self for method chaining
        """
        if element in self._elements:
            # Mark all current tags as removed
            for tag in self._elements[element]:
                self._tombstones.add((element, tag[0], tag[1]))

            # Remove from elements
            del self._elements[element]

        # Increment vector clock
        self.clock.increment()

        return self

    def contains(self, element: Any) -> bool:
        """Check if an element is in the set.

        Args:
            element: The element to check

        Returns:
            True if element is in the set
        """
        if element not in self._elements:
            return False

        # Element is in set if it has tags that aren't tombstoned
        for tag in self._elements[element]:
            if (element, tag[0], tag[1]) not in self._tombstones:
                return True

        return False

    def elements(self) -> Set[Any]:
        """Get all elements in the set.

        Returns:
            Set of all elements
        """
        result = set()
        for element in self._elements:
            if self.contains(element):
                result.add(element)
        return result

    def merge(self, other: "ORSet") -> "ORSet":
        """Merge another OR-Set into this one.

        Args:
            other: The other set to merge

        Returns:
            Self for method chaining
        """
        # Merge vector clocks
        self._merge_clocks(other)

        # Merge elements (union of tags)
        for element, tags in other._elements.items():
            if element not in self._elements:
                self._elements[element] = set()
            self._elements[element] |= tags

        # Merge tombstones (union)
        self._tombstones |= other._tombstones

        # Clean up elements that are fully tombstoned
        to_remove = []
        for element in self._elements:
            if not self.contains(element):
                to_remove.append(element)

        for element in to_remove:
            del self._elements[element]

        return self

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        # Convert elements dict to serializable format
        elements_dict = {}
        for element, tags in self._elements.items():
            elements_dict[str(element)] = list(tags)

        # Convert tombstones set to list
        tombstones_list = [
            {"element": str(t[0]), "unique_id": t[1], "device_id": t[2]}
            for t in self._tombstones
        ]

        return {
            "device_id": self.device_id,
            "clock": self.clock.to_dict(),
            "elements": elements_dict,
            "tombstones": tombstones_list
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ORSet":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            New ORSet instance
        """
        or_set = cls(device_id=data["device_id"])
        or_set.clock = VectorClock.from_dict(data["clock"])

        # Restore elements
        for element_str, tags_list in data.get("elements", {}).items():
            or_set._elements[element_str] = set(tuple(tag) for tag in tags_list)

        # Restore tombstones
        for tombstone in data.get("tombstones", []):
            or_set._tombstones.add((
                tombstone["element"],
                tombstone["unique_id"],
                tombstone["device_id"]
            ))

        return or_set

    def __len__(self) -> int:
        """Get the number of elements in the set."""
        return len(self.elements())

    def __contains__(self, element: Any) -> bool:
        """Check if an element is in the set."""
        return self.contains(element)

    def __repr__(self) -> str:
        """Detailed representation."""
        return f"ORSet(device={self.device_id}, elements={self.elements()}, clock={self.clock})"
