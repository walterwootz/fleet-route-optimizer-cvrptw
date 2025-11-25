"""Prediction Scheduler - Schedule periodic predictions.

Runs ML predictions on a schedule and stores results.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from .prediction_service import PredictionService
from ...models.database import SessionLocal
from ...models.railfleet.ml_models import MLPrediction
from ...config import get_logger

logger = get_logger(__name__)


class PredictionScheduler:
    """Scheduler for running predictions periodically.

    Example:
        >>> scheduler = PredictionScheduler()
        >>> scheduler.add_job(
        ...     "maintenance_check",
        ...     model_name="maintenance_predictor",
        ...     entity_type="Vehicle",
        ...     interval_hours=24
        ... )
        >>> await scheduler.start()
    """

    def __init__(self):
        self.jobs: Dict[str, Dict] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    def add_job(
        self,
        job_name: str,
        model_name: str,
        entity_type: str,
        interval_hours: int = 24,
        entity_filter: Optional[callable] = None,
    ):
        """Add a prediction job to the schedule.

        Args:
            job_name: Unique job name
            model_name: Name of model to use
            entity_type: Type of entity to predict
            interval_hours: Run interval in hours
            entity_filter: Optional function to filter entities
        """
        self.jobs[job_name] = {
            "model_name": model_name,
            "entity_type": entity_type,
            "interval_hours": interval_hours,
            "entity_filter": entity_filter,
            "last_run": None,
            "next_run": datetime.utcnow(),
        }
        logger.info(f"Added prediction job: {job_name}")

    async def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Prediction scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Prediction scheduler stopped")

    async def _run_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._process_jobs()
                await asyncio.sleep(3600)  # Check every hour
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                await asyncio.sleep(3600)

    async def _process_jobs(self):
        """Process all scheduled jobs."""
        now = datetime.utcnow()

        for job_name, job_config in self.jobs.items():
            if now >= job_config["next_run"]:
                logger.info(f"Running scheduled job: {job_name}")
                await self._run_job(job_name, job_config)

    async def _run_job(self, job_name: str, job_config: Dict):
        """Run a single prediction job.

        Args:
            job_name: Job name
            job_config: Job configuration
        """
        db = SessionLocal()

        try:
            # Get prediction service
            prediction_service = PredictionService(db)

            # Load model if not already loaded
            model_name = job_config["model_name"]
            if model_name not in prediction_service.get_loaded_models():
                # In production, load from configured path
                logger.warning(f"Model {model_name} not loaded, skipping job")
                return

            # Get entities to predict
            entity_type = job_config["entity_type"]
            entity_ids = self._get_entities(db, entity_type, job_config.get("entity_filter"))

            if not entity_ids:
                logger.info(f"No entities found for job {job_name}")
                return

            # Make predictions
            predictions = prediction_service.predict(model_name, entity_type, entity_ids)

            # Store predictions
            self._store_predictions(db, model_name, predictions)

            # Update job schedule
            from datetime import timedelta
            job_config["last_run"] = datetime.utcnow()
            job_config["next_run"] = datetime.utcnow() + timedelta(
                hours=job_config["interval_hours"]
            )

            logger.info(
                f"Job {job_name} completed: {len(predictions)} predictions made. "
                f"Next run: {job_config['next_run']}"
            )

        except Exception as e:
            logger.error(f"Job {job_name} failed: {e}", exc_info=True)

        finally:
            db.close()

    def _get_entities(
        self, db: Session, entity_type: str, entity_filter: Optional[callable]
    ) -> List[str]:
        """Get entity IDs to predict.

        Args:
            db: Database session
            entity_type: Type of entity
            entity_filter: Optional filter function

        Returns:
            List of entity IDs
        """
        # This is a simplified implementation
        # In production, query entities from database

        if entity_type == "Vehicle":
            from ...models.railfleet import Vehicle
            query = db.query(Vehicle.asset_id)
            if entity_filter:
                query = entity_filter(query)
            return [asset_id for (asset_id,) in query.all()]

        elif entity_type == "WorkOrder":
            from ...models.railfleet import WorkOrder
            query = db.query(WorkOrder.work_order_id)
            if entity_filter:
                query = entity_filter(query)
            return [wo_id for (wo_id,) in query.all()]

        elif entity_type == "Part":
            from ...models.railfleet import Part
            query = db.query(Part.part_number)
            if entity_filter:
                query = entity_filter(query)
            return [part_num for (part_num,) in query.all()]

        return []

    def _store_predictions(
        self, db: Session, model_name: str, predictions: List
    ):
        """Store predictions to database.

        Args:
            db: Database session
            model_name: Name of model
            predictions: List of Prediction objects
        """
        for pred in predictions:
            db_pred = MLPrediction(
                prediction_id=str(uuid4()),
                model_id="",  # Would be set from model metadata
                model_name=model_name,
                entity_type="",  # Set from context
                entity_id=pred.entity_id,
                prediction_value=str(pred.prediction),
                confidence=pred.confidence,
                probabilities=pred.probabilities,
                features={},
                metadata=pred.metadata,
            )
            db.add(db_pred)

        db.commit()
        logger.info(f"Stored {len(predictions)} predictions to database")


# Global scheduler instance
_scheduler: Optional[PredictionScheduler] = None


async def start_prediction_scheduler():
    """Start the global prediction scheduler.

    Returns:
        PredictionScheduler instance
    """
    global _scheduler

    if _scheduler and _scheduler._running:
        logger.warning("Prediction scheduler already running")
        return _scheduler

    _scheduler = PredictionScheduler()
    await _scheduler.start()
    return _scheduler


async def stop_prediction_scheduler():
    """Stop the global prediction scheduler."""
    global _scheduler

    if _scheduler:
        await _scheduler.stop()
        _scheduler = None


def get_prediction_scheduler() -> Optional[PredictionScheduler]:
    """Get the global prediction scheduler instance.

    Returns:
        PredictionScheduler instance or None
    """
    return _scheduler
