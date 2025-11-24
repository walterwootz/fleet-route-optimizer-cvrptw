"""Sync Engine - Local-first synchronization with CRDTs.

Handles device-to-device synchronization, conflict resolution, and
offline queue management using CRDT infrastructure.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..models.railfleet.crdt_metadata import CRDTMetadataModel, CRDTOperation
from ..models.crdt.vector_clock import VectorClock, VectorClockComparison
from ..models.crdt.base import CRDTType
from ..models.crdt.lww_register import LWWRegister
from ..models.crdt.or_set import ORSet
from ..models.crdt.counter import GCounter, PNCounter
from ..config import get_logger

logger = get_logger(__name__)


class SyncConflict:
    """Represents a sync conflict between two CRDT states."""

    def __init__(
        self,
        entity_type: str,
        entity_id: str,
        local_device: str,
        remote_device: str,
        local_clock: VectorClock,
        remote_clock: VectorClock,
        comparison: VectorClockComparison,
    ):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.local_device = local_device
        self.remote_device = remote_device
        self.local_clock = local_clock
        self.remote_clock = remote_clock
        self.comparison = comparison

    def is_concurrent(self) -> bool:
        """Check if this is a concurrent conflict."""
        return self.comparison == VectorClockComparison.CONCURRENT

    def __repr__(self):
        return (
            f"<SyncConflict {self.entity_type}:{self.entity_id} "
            f"{self.local_device} vs {self.remote_device} ({self.comparison.value})>"
        )


class SyncResult:
    """Result of a synchronization operation."""

    def __init__(self):
        self.entities_synced: int = 0
        self.conflicts_resolved: int = 0
        self.operations_applied: int = 0
        self.tombstones_processed: int = 0
        self.errors: List[str] = []
        self.conflicts: List[SyncConflict] = []

    def add_error(self, error: str):
        """Add an error message."""
        self.errors.append(error)
        logger.error(f"Sync error: {error}")

    def add_conflict(self, conflict: SyncConflict):
        """Add a detected conflict."""
        self.conflicts.append(conflict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "entities_synced": self.entities_synced,
            "conflicts_resolved": self.conflicts_resolved,
            "operations_applied": self.operations_applied,
            "tombstones_processed": self.tombstones_processed,
            "errors": self.errors,
            "conflicts": [
                {
                    "entity_type": c.entity_type,
                    "entity_id": c.entity_id,
                    "local_device": c.local_device,
                    "remote_device": c.remote_device,
                    "comparison": c.comparison.value,
                }
                for c in self.conflicts
            ],
        }


class SyncEngine:
    """Engine for local-first synchronization using CRDTs.

    Handles device-to-device sync, conflict resolution, and offline queue management.

    Example:
        >>> engine = SyncEngine(db)
        >>> result = engine.sync_from_remote(device_id, remote_states)
        >>> print(f"Synced {result.entities_synced} entities")
    """

    def __init__(self, db: Session):
        self.db = db

    def get_device_state(
        self, device_id: str, entity_types: Optional[List[str]] = None
    ) -> List[CRDTMetadataModel]:
        """Get all CRDT metadata for a device.

        Args:
            device_id: Device identifier
            entity_types: Optional list of entity types to filter

        Returns:
            List of CRDT metadata records
        """
        query = self.db.query(CRDTMetadataModel).filter(
            CRDTMetadataModel.device_id == device_id
        )

        if entity_types:
            query = query.filter(CRDTMetadataModel.entity_type.in_(entity_types))

        return query.all()

    def get_entity_state(
        self, entity_type: str, entity_id: str, device_id: Optional[str] = None
    ) -> List[CRDTMetadataModel]:
        """Get CRDT state for a specific entity.

        Args:
            entity_type: Type of entity (e.g., "Vehicle", "WorkOrder")
            entity_id: Entity identifier
            device_id: Optional device filter

        Returns:
            List of CRDT metadata records (one per device that modified the entity)
        """
        query = self.db.query(CRDTMetadataModel).filter(
            and_(
                CRDTMetadataModel.entity_type == entity_type,
                CRDTMetadataModel.entity_id == entity_id,
            )
        )

        if device_id:
            query = query.filter(CRDTMetadataModel.device_id == device_id)

        return query.all()

    def merge_entity_states(
        self,
        entity_type: str,
        entity_id: str,
        crdt_type: CRDTType,
        device_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Merge all CRDT states for an entity across all devices.

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            crdt_type: Type of CRDT (LWW_REGISTER, OR_SET, etc.)
            device_id: Current device ID for merge context

        Returns:
            Merged CRDT data or None if no states found
        """
        states = self.get_entity_state(entity_type, entity_id)

        if not states:
            return None

        # Create CRDT instance based on type
        if crdt_type == CRDTType.LWW_REGISTER:
            merged_crdt = self._merge_lww_states(states, device_id)
        elif crdt_type == CRDTType.OR_SET:
            merged_crdt = self._merge_or_set_states(states, device_id)
        elif crdt_type == CRDTType.G_COUNTER:
            merged_crdt = self._merge_gcounter_states(states, device_id)
        elif crdt_type == CRDTType.PN_COUNTER:
            merged_crdt = self._merge_pncounter_states(states, device_id)
        else:
            logger.warning(f"Unknown CRDT type: {crdt_type}")
            return None

        return merged_crdt.to_dict() if merged_crdt else None

    def _merge_lww_states(
        self, states: List[CRDTMetadataModel], device_id: str
    ) -> LWWRegister:
        """Merge multiple LWW-Register states."""
        merged = LWWRegister(device_id=device_id)

        for state in states:
            remote_register = LWWRegister.from_dict(state.crdt_data, device_id)
            merged = merged.merge(remote_register)

        return merged

    def _merge_or_set_states(
        self, states: List[CRDTMetadataModel], device_id: str
    ) -> ORSet:
        """Merge multiple OR-Set states."""
        merged = ORSet(device_id=device_id)

        for state in states:
            remote_set = ORSet.from_dict(state.crdt_data, device_id)
            merged = merged.merge(remote_set)

        return merged

    def _merge_gcounter_states(
        self, states: List[CRDTMetadataModel], device_id: str
    ) -> GCounter:
        """Merge multiple GCounter states."""
        merged = GCounter(device_id=device_id)

        for state in states:
            remote_counter = GCounter.from_dict(state.crdt_data, device_id)
            merged = merged.merge(remote_counter)

        return merged

    def _merge_pncounter_states(
        self, states: List[CRDTMetadataModel], device_id: str
    ) -> PNCounter:
        """Merge multiple PNCounter states."""
        merged = PNCounter(device_id=device_id)

        for state in states:
            remote_counter = PNCounter.from_dict(state.crdt_data, device_id)
            merged = merged.merge(remote_counter)

        return merged

    def sync_from_remote(
        self,
        local_device_id: str,
        remote_states: List[Dict[str, Any]],
    ) -> SyncResult:
        """Sync remote CRDT states to local database.

        Args:
            local_device_id: Local device identifier
            remote_states: List of remote CRDT metadata dictionaries

        Returns:
            SyncResult with statistics and conflicts
        """
        result = SyncResult()

        for remote_state in remote_states:
            try:
                self._sync_entity_state(local_device_id, remote_state, result)
            except Exception as e:
                result.add_error(f"Failed to sync {remote_state.get('entity_id')}: {e}")
                logger.exception("Sync error")

        self.db.commit()
        logger.info(
            f"Sync complete: {result.entities_synced} entities, "
            f"{result.conflicts_resolved} conflicts resolved"
        )

        return result

    def _sync_entity_state(
        self,
        local_device_id: str,
        remote_state: Dict[str, Any],
        result: SyncResult,
    ):
        """Sync a single entity state from remote."""
        entity_type = remote_state["entity_type"]
        entity_id = remote_state["entity_id"]
        remote_device_id = remote_state["device_id"]

        # Get local state
        local_state = (
            self.db.query(CRDTMetadataModel)
            .filter(
                and_(
                    CRDTMetadataModel.entity_type == entity_type,
                    CRDTMetadataModel.entity_id == entity_id,
                    CRDTMetadataModel.device_id == remote_device_id,
                )
            )
            .first()
        )

        # Create vector clocks
        remote_clock = VectorClock.from_dict(
            remote_state["vector_clock"], remote_device_id
        )

        if local_state:
            local_clock = VectorClock.from_dict(
                local_state.vector_clock, local_device_id
            )
            comparison = local_clock.compare(remote_clock)

            # Detect conflicts
            if comparison == VectorClockComparison.CONCURRENT:
                conflict = SyncConflict(
                    entity_type,
                    entity_id,
                    local_device_id,
                    remote_device_id,
                    local_clock,
                    remote_clock,
                    comparison,
                )
                result.add_conflict(conflict)
                result.conflicts_resolved += 1

            # Update if remote is newer or concurrent
            if comparison in (
                VectorClockComparison.BEFORE,
                VectorClockComparison.CONCURRENT,
            ):
                local_state.vector_clock = remote_clock.to_dict()
                local_state.crdt_data = remote_state["crdt_data"]
                local_state.tombstone = remote_state.get("tombstone", False)
                local_state.updated_at = datetime.utcnow()
                result.entities_synced += 1

                if remote_state.get("tombstone"):
                    result.tombstones_processed += 1
        else:
            # Create new local state
            new_state = CRDTMetadataModel(
                entity_type=entity_type,
                entity_id=entity_id,
                device_id=remote_device_id,
                vector_clock=remote_state["vector_clock"],
                crdt_data=remote_state["crdt_data"],
                tombstone=remote_state.get("tombstone", False),
            )
            self.db.add(new_state)
            result.entities_synced += 1

            if remote_state.get("tombstone"):
                result.tombstones_processed += 1

    def get_changes_since(
        self, device_id: str, since: datetime
    ) -> List[CRDTMetadataModel]:
        """Get all CRDT changes for a device since a timestamp.

        Args:
            device_id: Device identifier
            since: Timestamp to get changes after

        Returns:
            List of CRDT metadata records modified after timestamp
        """
        return (
            self.db.query(CRDTMetadataModel)
            .filter(
                and_(
                    CRDTMetadataModel.device_id == device_id,
                    CRDTMetadataModel.updated_at > since,
                )
            )
            .order_by(CRDTMetadataModel.updated_at)
            .all()
        )

    def record_operation(
        self,
        entity_type: str,
        entity_id: str,
        device_id: str,
        operation_type: str,
        operation_data: Dict[str, Any],
        vector_clock: VectorClock,
    ) -> CRDTOperation:
        """Record a CRDT operation for auditing.

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            device_id: Device that performed operation
            operation_type: Type of operation (set, add, remove, increment, etc.)
            operation_data: Operation-specific data
            vector_clock: Vector clock at time of operation

        Returns:
            Created operation record
        """
        operation = CRDTOperation(
            operation_id=str(uuid4()),
            entity_type=entity_type,
            entity_id=entity_id,
            device_id=device_id,
            operation_type=operation_type,
            operation_data=operation_data,
            vector_clock=vector_clock.to_dict(),
        )
        self.db.add(operation)
        self.db.commit()

        return operation

    def mark_as_tombstone(
        self, entity_type: str, entity_id: str, device_id: str
    ) -> bool:
        """Mark an entity as deleted (tombstone).

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier
            device_id: Device that deleted the entity

        Returns:
            True if marked, False if not found
        """
        state = (
            self.db.query(CRDTMetadataModel)
            .filter(
                and_(
                    CRDTMetadataModel.entity_type == entity_type,
                    CRDTMetadataModel.entity_id == entity_id,
                    CRDTMetadataModel.device_id == device_id,
                )
            )
            .first()
        )

        if state:
            state.tombstone = True
            state.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Marked {entity_type}:{entity_id} as tombstone")
            return True

        return False

    def get_active_entities(
        self, entity_type: str, device_id: Optional[str] = None
    ) -> List[CRDTMetadataModel]:
        """Get all active (non-tombstoned) entities.

        Args:
            entity_type: Type of entity
            device_id: Optional device filter

        Returns:
            List of active CRDT metadata records
        """
        query = self.db.query(CRDTMetadataModel).filter(
            and_(
                CRDTMetadataModel.entity_type == entity_type,
                CRDTMetadataModel.tombstone == False,
            )
        )

        if device_id:
            query = query.filter(CRDTMetadataModel.device_id == device_id)

        return query.all()
