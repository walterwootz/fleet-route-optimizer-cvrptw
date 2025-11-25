"""Conflict Resolution - Custom strategies for CRDT conflict resolution.

Provides additional conflict resolution strategies beyond automatic CRDT merge,
including business-logic-specific resolution rules.
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from ..models.crdt.vector_clock import VectorClock, VectorClockComparison
from ..models.crdt.lww_register import LWWRegister
from ..config import get_logger

logger = get_logger(__name__)


class ConflictResolutionStrategy(str, Enum):
    """Conflict resolution strategies."""

    # Automatic CRDT merge (default)
    CRDT_MERGE = "crdt_merge"

    # Custom strategies
    NEWEST_WINS = "newest_wins"
    OLDEST_WINS = "oldest_wins"
    PRIORITY_DEVICE = "priority_device"
    MANUAL = "manual"
    CUSTOM = "custom"


class ConflictContext:
    """Context information for conflict resolution.

    Contains all information needed to make resolution decisions.
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        field_name: str,
        local_value: Any,
        remote_value: Any,
        local_timestamp: datetime,
        remote_timestamp: datetime,
        local_device: str,
        remote_device: str,
        local_clock: VectorClock,
        remote_clock: VectorClock,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.field_name = field_name
        self.local_value = local_value
        self.remote_value = remote_value
        self.local_timestamp = local_timestamp
        self.remote_timestamp = remote_timestamp
        self.local_device = local_device
        self.remote_device = remote_device
        self.local_clock = local_clock
        self.remote_clock = remote_clock

    def is_concurrent(self) -> bool:
        """Check if the conflict is concurrent."""
        return (
            self.local_clock.compare(self.remote_clock)
            == VectorClockComparison.CONCURRENT
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "field_name": self.field_name,
            "local_value": self.local_value,
            "remote_value": self.remote_value,
            "local_timestamp": self.local_timestamp.isoformat(),
            "remote_timestamp": self.remote_timestamp.isoformat(),
            "local_device": self.local_device,
            "remote_device": self.remote_device,
            "is_concurrent": self.is_concurrent(),
        }


class ConflictResolution:
    """Result of conflict resolution."""

    def __init__(
        self,
        strategy: ConflictResolutionStrategy,
        resolved_value: Any,
        winner_device: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.strategy = strategy
        self.resolved_value = resolved_value
        self.winner_device = winner_device
        self.metadata = metadata or {}
        self.resolved_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "strategy": self.strategy.value,
            "resolved_value": self.resolved_value,
            "winner_device": self.winner_device,
            "metadata": self.metadata,
            "resolved_at": self.resolved_at.isoformat(),
        }


class ConflictResolver:
    """Resolves conflicts using various strategies.

    Example:
        >>> resolver = ConflictResolver()
        >>> resolution = resolver.resolve(
        ...     context,
        ...     strategy=ConflictResolutionStrategy.NEWEST_WINS
        ... )
        >>> print(f"Winner: {resolution.winner_device}")
    """

    def __init__(self):
        self._custom_handlers: Dict[str, Callable] = {}
        self._priority_devices: List[str] = []

    def set_priority_devices(self, device_ids: List[str]):
        """Set device priority order for PRIORITY_DEVICE strategy.

        Args:
            device_ids: List of device IDs in priority order (highest first)
        """
        self._priority_devices = device_ids
        logger.info(f"Set device priority: {device_ids}")

    def register_custom_handler(
        self, entity_type: str, handler: Callable[[ConflictContext], Any]
    ):
        """Register custom conflict resolution handler for entity type.

        Args:
            entity_type: Type of entity (e.g., "Vehicle", "WorkOrder")
            handler: Function that takes ConflictContext and returns resolved value
        """
        self._custom_handlers[entity_type] = handler
        logger.info(f"Registered custom handler for {entity_type}")

    def resolve(
        self,
        context: ConflictContext,
        strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.CRDT_MERGE,
    ) -> ConflictResolution:
        """Resolve a conflict using specified strategy.

        Args:
            context: Conflict context with all information
            strategy: Resolution strategy to use

        Returns:
            ConflictResolution with resolved value and metadata
        """
        if strategy == ConflictResolutionStrategy.CRDT_MERGE:
            return self._resolve_crdt_merge(context)
        elif strategy == ConflictResolutionStrategy.NEWEST_WINS:
            return self._resolve_newest_wins(context)
        elif strategy == ConflictResolutionStrategy.OLDEST_WINS:
            return self._resolve_oldest_wins(context)
        elif strategy == ConflictResolutionStrategy.PRIORITY_DEVICE:
            return self._resolve_priority_device(context)
        elif strategy == ConflictResolutionStrategy.CUSTOM:
            return self._resolve_custom(context)
        elif strategy == ConflictResolutionStrategy.MANUAL:
            return self._resolve_manual(context)
        else:
            logger.warning(f"Unknown strategy {strategy}, falling back to CRDT merge")
            return self._resolve_crdt_merge(context)

    def _resolve_crdt_merge(self, context: ConflictContext) -> ConflictResolution:
        """Resolve using CRDT LWW-Register merge."""
        # Create LWW registers for both values
        local_register = LWWRegister(device_id=context.local_device)
        local_register.set(context.local_value, context.local_timestamp)
        local_register.clock = context.local_clock

        remote_register = LWWRegister(device_id=context.remote_device)
        remote_register.set(context.remote_value, context.remote_timestamp)
        remote_register.clock = context.remote_clock

        # Merge using CRDT semantics
        merged = local_register.merge(remote_register)
        winner_device = merged._lww_value.device_id

        return ConflictResolution(
            strategy=ConflictResolutionStrategy.CRDT_MERGE,
            resolved_value=merged.get(),
            winner_device=winner_device,
            metadata={
                "local_timestamp": context.local_timestamp.isoformat(),
                "remote_timestamp": context.remote_timestamp.isoformat(),
            },
        )

    def _resolve_newest_wins(self, context: ConflictContext) -> ConflictResolution:
        """Resolve by choosing newest value."""
        if context.remote_timestamp > context.local_timestamp:
            winner_device = context.remote_device
            resolved_value = context.remote_value
        elif context.local_timestamp > context.remote_timestamp:
            winner_device = context.local_device
            resolved_value = context.local_value
        else:
            # Equal timestamps - use device ID tiebreaker
            if context.remote_device > context.local_device:
                winner_device = context.remote_device
                resolved_value = context.remote_value
            else:
                winner_device = context.local_device
                resolved_value = context.local_value

        return ConflictResolution(
            strategy=ConflictResolutionStrategy.NEWEST_WINS,
            resolved_value=resolved_value,
            winner_device=winner_device,
            metadata={
                "local_timestamp": context.local_timestamp.isoformat(),
                "remote_timestamp": context.remote_timestamp.isoformat(),
            },
        )

    def _resolve_oldest_wins(self, context: ConflictContext) -> ConflictResolution:
        """Resolve by choosing oldest value."""
        if context.remote_timestamp < context.local_timestamp:
            winner_device = context.remote_device
            resolved_value = context.remote_value
        elif context.local_timestamp < context.remote_timestamp:
            winner_device = context.local_device
            resolved_value = context.local_value
        else:
            # Equal timestamps - use device ID tiebreaker
            if context.remote_device < context.local_device:
                winner_device = context.remote_device
                resolved_value = context.remote_value
            else:
                winner_device = context.local_device
                resolved_value = context.local_value

        return ConflictResolution(
            strategy=ConflictResolutionStrategy.OLDEST_WINS,
            resolved_value=resolved_value,
            winner_device=winner_device,
            metadata={
                "local_timestamp": context.local_timestamp.isoformat(),
                "remote_timestamp": context.remote_timestamp.isoformat(),
            },
        )

    def _resolve_priority_device(
        self, context: ConflictContext
    ) -> ConflictResolution:
        """Resolve by device priority."""
        if not self._priority_devices:
            logger.warning("No priority devices configured, falling back to CRDT merge")
            return self._resolve_crdt_merge(context)

        # Check if devices are in priority list
        local_priority = (
            self._priority_devices.index(context.local_device)
            if context.local_device in self._priority_devices
            else float("inf")
        )
        remote_priority = (
            self._priority_devices.index(context.remote_device)
            if context.remote_device in self._priority_devices
            else float("inf")
        )

        # Lower index = higher priority
        if remote_priority < local_priority:
            winner_device = context.remote_device
            resolved_value = context.remote_value
        else:
            winner_device = context.local_device
            resolved_value = context.local_value

        return ConflictResolution(
            strategy=ConflictResolutionStrategy.PRIORITY_DEVICE,
            resolved_value=resolved_value,
            winner_device=winner_device,
            metadata={
                "local_priority": local_priority,
                "remote_priority": remote_priority,
            },
        )

    def _resolve_custom(self, context: ConflictContext) -> ConflictResolution:
        """Resolve using custom handler."""
        handler = self._custom_handlers.get(context.entity_type)

        if not handler:
            logger.warning(
                f"No custom handler for {context.entity_type}, "
                f"falling back to CRDT merge"
            )
            return self._resolve_crdt_merge(context)

        try:
            resolved_value = handler(context)
            # Custom handler returns the resolved value, we infer winner from value match
            if resolved_value == context.remote_value:
                winner_device = context.remote_device
            else:
                winner_device = context.local_device

            return ConflictResolution(
                strategy=ConflictResolutionStrategy.CUSTOM,
                resolved_value=resolved_value,
                winner_device=winner_device,
                metadata={"handler": handler.__name__},
            )
        except Exception as e:
            logger.error(f"Custom handler failed: {e}", exc_info=True)
            return self._resolve_crdt_merge(context)

    def _resolve_manual(self, context: ConflictContext) -> ConflictResolution:
        """Mark conflict for manual resolution.

        Returns local value as temporary resolution, but marks it as needing manual review.
        """
        return ConflictResolution(
            strategy=ConflictResolutionStrategy.MANUAL,
            resolved_value=context.local_value,
            winner_device=context.local_device,
            metadata={
                "requires_manual_review": True,
                "local_value": context.local_value,
                "remote_value": context.remote_value,
            },
        )


# Global resolver instance
_resolver = ConflictResolver()


def get_conflict_resolver() -> ConflictResolver:
    """Get global conflict resolver.

    Returns:
        ConflictResolver instance
    """
    return _resolver
