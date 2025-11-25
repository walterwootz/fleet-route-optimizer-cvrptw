"""Sync Queue - Offline operation queue for local-first sync.

Manages operations performed offline that need to be synced when
device comes back online.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..config import get_logger

logger = get_logger(__name__)


class SyncStatus(str, Enum):
    """Status of a queued sync operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


class SyncPriority(str, Enum):
    """Priority of sync operations."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class QueuedOperation:
    """Represents an operation queued for synchronization.

    Example:
        >>> op = QueuedOperation(
        ...     device_id="device-123",
        ...     operation_type="vehicle_update",
        ...     entity_type="Vehicle",
        ...     entity_id="V001",
        ...     payload={"status": "in_service"},
        ...     priority=SyncPriority.NORMAL
        ... )
    """

    def __init__(
        self,
        device_id: str,
        operation_type: str,
        entity_type: str,
        entity_id: str,
        payload: Dict[str, Any],
        priority: SyncPriority = SyncPriority.NORMAL,
        operation_id: Optional[str] = None,
    ):
        self.operation_id = operation_id or str(uuid4())
        self.device_id = device_id
        self.operation_type = operation_type
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.payload = payload
        self.priority = priority
        self.status = SyncStatus.PENDING
        self.retry_count = 0
        self.max_retries = 3
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.error_message: Optional[str] = None

    def mark_in_progress(self):
        """Mark operation as in progress."""
        self.status = SyncStatus.IN_PROGRESS
        self.updated_at = datetime.utcnow()

    def mark_completed(self):
        """Mark operation as completed."""
        self.status = SyncStatus.COMPLETED
        self.updated_at = datetime.utcnow()

    def mark_failed(self, error: str):
        """Mark operation as failed."""
        self.error_message = error
        self.retry_count += 1
        self.updated_at = datetime.utcnow()

        if self.retry_count >= self.max_retries:
            self.status = SyncStatus.FAILED
        else:
            self.status = SyncStatus.RETRY

    def can_retry(self) -> bool:
        """Check if operation can be retried."""
        return (
            self.status == SyncStatus.RETRY
            and self.retry_count < self.max_retries
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "operation_id": self.operation_id,
            "device_id": self.device_id,
            "operation_type": self.operation_type,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error_message": self.error_message,
        }


class SyncQueue:
    """Queue for managing offline operations.

    Stores operations performed offline and processes them when
    device comes back online.

    Example:
        >>> queue = SyncQueue(device_id="device-123")
        >>> queue.enqueue(
        ...     operation_type="vehicle_update",
        ...     entity_type="Vehicle",
        ...     entity_id="V001",
        ...     payload={"status": "in_service"}
        ... )
        >>> pending = queue.get_pending_operations()
        >>> for op in pending:
        ...     try:
        ...         sync_engine.apply(op)
        ...         queue.mark_completed(op.operation_id)
        ...     except Exception as e:
        ...         queue.mark_failed(op.operation_id, str(e))
    """

    def __init__(self, device_id: str):
        self.device_id = device_id
        self._queue: Dict[str, QueuedOperation] = {}

    def enqueue(
        self,
        operation_type: str,
        entity_type: str,
        entity_id: str,
        payload: Dict[str, Any],
        priority: SyncPriority = SyncPriority.NORMAL,
    ) -> QueuedOperation:
        """Add an operation to the queue.

        Args:
            operation_type: Type of operation (create, update, delete, etc.)
            entity_type: Type of entity (Vehicle, WorkOrder, etc.)
            entity_id: Entity identifier
            payload: Operation payload/data
            priority: Operation priority

        Returns:
            Queued operation
        """
        operation = QueuedOperation(
            device_id=self.device_id,
            operation_type=operation_type,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            priority=priority,
        )

        self._queue[operation.operation_id] = operation
        logger.info(
            f"Enqueued operation {operation.operation_id}: "
            f"{operation_type} on {entity_type}:{entity_id}"
        )

        return operation

    def get_pending_operations(
        self, limit: Optional[int] = None
    ) -> List[QueuedOperation]:
        """Get pending operations sorted by priority and creation time.

        Args:
            limit: Maximum number of operations to return

        Returns:
            List of pending operations
        """
        pending = [
            op
            for op in self._queue.values()
            if op.status in (SyncStatus.PENDING, SyncStatus.RETRY)
        ]

        # Sort by priority (higher first) then by creation time
        priority_order = {
            SyncPriority.CRITICAL: 4,
            SyncPriority.HIGH: 3,
            SyncPriority.NORMAL: 2,
            SyncPriority.LOW: 1,
        }

        pending.sort(
            key=lambda op: (priority_order[op.priority], op.created_at),
            reverse=True,
        )

        if limit:
            return pending[:limit]
        return pending

    def get_operation(self, operation_id: str) -> Optional[QueuedOperation]:
        """Get a specific operation by ID.

        Args:
            operation_id: Operation identifier

        Returns:
            Operation or None if not found
        """
        return self._queue.get(operation_id)

    def mark_in_progress(self, operation_id: str) -> bool:
        """Mark operation as in progress.

        Args:
            operation_id: Operation identifier

        Returns:
            True if marked, False if not found
        """
        operation = self._queue.get(operation_id)
        if operation:
            operation.mark_in_progress()
            return True
        return False

    def mark_completed(self, operation_id: str) -> bool:
        """Mark operation as completed.

        Args:
            operation_id: Operation identifier

        Returns:
            True if marked, False if not found
        """
        operation = self._queue.get(operation_id)
        if operation:
            operation.mark_completed()
            logger.info(f"Operation {operation_id} completed")
            return True
        return False

    def mark_failed(self, operation_id: str, error: str) -> bool:
        """Mark operation as failed.

        Args:
            operation_id: Operation identifier
            error: Error message

        Returns:
            True if marked, False if not found
        """
        operation = self._queue.get(operation_id)
        if operation:
            operation.mark_failed(error)
            logger.warning(
                f"Operation {operation_id} failed (attempt {operation.retry_count}): {error}"
            )
            return True
        return False

    def clear_completed(self) -> int:
        """Remove completed operations from queue.

        Returns:
            Number of operations removed
        """
        completed_ids = [
            op_id
            for op_id, op in self._queue.items()
            if op.status == SyncStatus.COMPLETED
        ]

        for op_id in completed_ids:
            del self._queue[op_id]

        if completed_ids:
            logger.info(f"Cleared {len(completed_ids)} completed operations")

        return len(completed_ids)

    def clear_failed(self) -> int:
        """Remove permanently failed operations from queue.

        Returns:
            Number of operations removed
        """
        failed_ids = [
            op_id
            for op_id, op in self._queue.items()
            if op.status == SyncStatus.FAILED
        ]

        for op_id in failed_ids:
            del self._queue[op_id]

        if failed_ids:
            logger.info(f"Cleared {len(failed_ids)} failed operations")

        return len(failed_ids)

    def get_queue_stats(self) -> Dict[str, int]:
        """Get queue statistics.

        Returns:
            Dictionary with counts per status
        """
        stats = {
            "total": len(self._queue),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "retry": 0,
        }

        for operation in self._queue.values():
            stats[operation.status.value] += 1

        return stats

    def get_operations_by_entity(
        self, entity_type: str, entity_id: str
    ) -> List[QueuedOperation]:
        """Get all operations for a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity identifier

        Returns:
            List of operations for the entity
        """
        return [
            op
            for op in self._queue.values()
            if op.entity_type == entity_type and op.entity_id == entity_id
        ]


class SyncQueueManager:
    """Manager for multiple device sync queues.

    Manages sync queues for multiple devices and provides
    centralized queue operations.
    """

    def __init__(self):
        self._queues: Dict[str, SyncQueue] = {}

    def get_queue(self, device_id: str) -> SyncQueue:
        """Get or create a sync queue for a device.

        Args:
            device_id: Device identifier

        Returns:
            Sync queue for the device
        """
        if device_id not in self._queues:
            self._queues[device_id] = SyncQueue(device_id)
            logger.info(f"Created sync queue for device {device_id}")

        return self._queues[device_id]

    def get_all_pending_operations(self) -> Dict[str, List[QueuedOperation]]:
        """Get pending operations for all devices.

        Returns:
            Dictionary mapping device_id to list of pending operations
        """
        return {
            device_id: queue.get_pending_operations()
            for device_id, queue in self._queues.items()
        }

    def get_global_stats(self) -> Dict[str, Any]:
        """Get statistics across all queues.

        Returns:
            Dictionary with global statistics
        """
        total_stats = {
            "total_devices": len(self._queues),
            "total_operations": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0,
            "retry": 0,
        }

        for queue in self._queues.values():
            stats = queue.get_queue_stats()
            total_stats["total_operations"] += stats["total"]
            total_stats["pending"] += stats["pending"]
            total_stats["in_progress"] += stats["in_progress"]
            total_stats["completed"] += stats["completed"]
            total_stats["failed"] += stats["failed"]
            total_stats["retry"] += stats["retry"]

        return total_stats


# Global queue manager instance
_queue_manager = SyncQueueManager()


def get_sync_queue(device_id: str) -> SyncQueue:
    """Get sync queue for a device.

    Args:
        device_id: Device identifier

    Returns:
        Sync queue instance
    """
    return _queue_manager.get_queue(device_id)


def get_queue_manager() -> SyncQueueManager:
    """Get global queue manager.

    Returns:
        SyncQueueManager instance
    """
    return _queue_manager
