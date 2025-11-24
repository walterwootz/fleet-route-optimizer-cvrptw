"""Sync Worker - Background worker for processing sync queues.

Periodically processes offline operation queues and syncs with server.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models.database import SessionLocal
from ..services.sync_engine import SyncEngine
from ..services.sync_queue import get_queue_manager, SyncStatus
from ..config import get_logger

logger = get_logger(__name__)


class SyncWorker:
    """Background worker for processing sync queues.

    Runs periodically to:
    1. Process pending operations from offline queues
    2. Retry failed operations
    3. Clean up old completed operations

    Example:
        >>> worker = SyncWorker(interval_seconds=30)
        >>> await worker.start()
    """

    def __init__(
        self,
        interval_seconds: int = 30,
        max_operations_per_run: int = 100,
        cleanup_after_hours: int = 24,
    ):
        self.interval_seconds = interval_seconds
        self.max_operations_per_run = max_operations_per_run
        self.cleanup_after_hours = cleanup_after_hours
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.stats = {
            "runs": 0,
            "operations_processed": 0,
            "operations_succeeded": 0,
            "operations_failed": 0,
            "operations_cleaned": 0,
        }

    async def start(self):
        """Start the background worker."""
        if self._running:
            logger.warning("Sync worker already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(
            f"Sync worker started (interval: {self.interval_seconds}s, "
            f"max ops: {self.max_operations_per_run})"
        )

    async def stop(self):
        """Stop the background worker."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Sync worker stopped")

    async def _run_loop(self):
        """Main worker loop."""
        while self._running:
            try:
                await self._process_sync_queues()
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync worker loop: {e}", exc_info=True)
                await asyncio.sleep(self.interval_seconds)

    async def _process_sync_queues(self):
        """Process all device sync queues."""
        self.stats["runs"] += 1
        start_time = datetime.utcnow()

        logger.debug("Processing sync queues...")

        # Get all pending operations across devices
        queue_manager = get_queue_manager()
        all_pending = queue_manager.get_all_pending_operations()

        if not all_pending:
            logger.debug("No pending operations to process")
            return

        # Create database session
        db = SessionLocal()

        try:
            for device_id, operations in all_pending.items():
                # Limit operations per device
                operations = operations[: self.max_operations_per_run]

                logger.info(
                    f"Processing {len(operations)} operations for device {device_id}"
                )

                for operation in operations:
                    try:
                        await self._process_operation(db, device_id, operation)
                        self.stats["operations_processed"] += 1
                        self.stats["operations_succeeded"] += 1
                    except Exception as e:
                        logger.error(
                            f"Failed to process operation {operation.operation_id}: {e}"
                        )
                        self.stats["operations_processed"] += 1
                        self.stats["operations_failed"] += 1

            # Cleanup old completed operations
            await self._cleanup_old_operations()

            db.commit()

        except Exception as e:
            logger.error(f"Error processing sync queues: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

        elapsed = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"Sync queue processing completed in {elapsed:.2f}s")

    async def _process_operation(
        self, db: Session, device_id: str, operation: Any
    ):
        """Process a single queued operation.

        Args:
            db: Database session
            device_id: Device identifier
            operation: Queued operation
        """
        queue = get_queue_manager().get_queue(device_id)

        try:
            # Mark as in progress
            queue.mark_in_progress(operation.operation_id)

            # Apply operation based on type
            if operation.operation_type == "vehicle_update":
                await self._apply_vehicle_update(db, operation)
            elif operation.operation_type == "workorder_update":
                await self._apply_workorder_update(db, operation)
            elif operation.operation_type == "stock_move":
                await self._apply_stock_move(db, operation)
            else:
                logger.warning(
                    f"Unknown operation type: {operation.operation_type}"
                )

            # Mark as completed
            queue.mark_completed(operation.operation_id)

            logger.debug(
                f"Operation {operation.operation_id} completed successfully"
            )

        except Exception as e:
            # Mark as failed
            queue.mark_failed(operation.operation_id, str(e))
            raise

    async def _apply_vehicle_update(self, db: Session, operation: Any):
        """Apply vehicle update operation.

        Args:
            db: Database session
            operation: Operation to apply
        """
        # This is a placeholder - actual implementation would:
        # 1. Get vehicle entity
        # 2. Apply CRDT merge
        # 3. Update database
        # 4. Publish event

        logger.debug(
            f"Applying vehicle update: {operation.entity_id} "
            f"with payload {operation.payload}"
        )

        # Simulate async operation
        await asyncio.sleep(0.01)

    async def _apply_workorder_update(self, db: Session, operation: Any):
        """Apply work order update operation.

        Args:
            db: Database session
            operation: Operation to apply
        """
        logger.debug(
            f"Applying work order update: {operation.entity_id} "
            f"with payload {operation.payload}"
        )

        # Simulate async operation
        await asyncio.sleep(0.01)

    async def _apply_stock_move(self, db: Session, operation: Any):
        """Apply stock move operation.

        Args:
            db: Database session
            operation: Operation to apply
        """
        logger.debug(
            f"Applying stock move: {operation.entity_id} "
            f"with payload {operation.payload}"
        )

        # Simulate async operation
        await asyncio.sleep(0.01)

    async def _cleanup_old_operations(self):
        """Clean up old completed operations."""
        queue_manager = get_queue_manager()
        cutoff_time = datetime.utcnow() - timedelta(hours=self.cleanup_after_hours)

        cleaned = 0
        for device_id, queue in queue_manager._queues.items():
            # Find old completed operations
            old_operations = [
                op_id
                for op_id, op in queue._queue.items()
                if op.status == SyncStatus.COMPLETED
                and op.updated_at < cutoff_time
            ]

            # Remove them
            for op_id in old_operations:
                del queue._queue[op_id]
                cleaned += 1

        if cleaned > 0:
            self.stats["operations_cleaned"] += cleaned
            logger.info(f"Cleaned up {cleaned} old completed operations")

    def get_stats(self) -> Dict[str, Any]:
        """Get worker statistics.

        Returns:
            Dictionary with worker stats
        """
        return {
            **self.stats,
            "is_running": self._running,
            "interval_seconds": self.interval_seconds,
            "max_operations_per_run": self.max_operations_per_run,
        }


# Global worker instance
_worker: Optional[SyncWorker] = None


async def start_sync_worker(
    interval_seconds: int = 30,
    max_operations_per_run: int = 100,
    cleanup_after_hours: int = 24,
):
    """Start the global sync worker.

    Args:
        interval_seconds: Interval between runs
        max_operations_per_run: Max operations to process per run
        cleanup_after_hours: Hours after which to cleanup completed ops

    Returns:
        SyncWorker instance
    """
    global _worker

    if _worker and _worker._running:
        logger.warning("Sync worker already running")
        return _worker

    _worker = SyncWorker(
        interval_seconds=interval_seconds,
        max_operations_per_run=max_operations_per_run,
        cleanup_after_hours=cleanup_after_hours,
    )

    await _worker.start()
    return _worker


async def stop_sync_worker():
    """Stop the global sync worker."""
    global _worker

    if _worker:
        await _worker.stop()
        _worker = None


def get_sync_worker() -> Optional[SyncWorker]:
    """Get the global sync worker instance.

    Returns:
        SyncWorker instance or None if not started
    """
    return _worker
