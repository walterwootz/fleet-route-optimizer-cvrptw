"""Example: Train maintenance prediction model.

This script demonstrates how to train a maintenance prediction model
using historical vehicle data.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.models.database import SessionLocal
from src.services.ml.training_pipeline import TrainingPipeline
from src.services.ml.models.maintenance_predictor import MaintenancePredictor
from src.config import get_logger

logger = get_logger(__name__)


def generate_sample_labels(entity_ids: list, db: Session) -> list:
    """Generate sample labels for training.

    In production, labels would be derived from actual maintenance records.
    This is a simplified example.

    Args:
        entity_ids: List of vehicle IDs
        db: Database session

    Returns:
        List of labels (1=needs maintenance, 0=ok)
    """
    # This is a placeholder - in production, you would:
    # 1. Query maintenance records for each vehicle
    # 2. Check if maintenance occurred within 30 days after feature extraction
    # 3. Label accordingly

    labels = []
    for entity_id in entity_ids:
        # Placeholder logic - replace with actual data
        # For now, randomly assign labels for demonstration
        import random
        label = random.choice([0, 1])
        labels.append(label)

    return labels


def main():
    """Train maintenance prediction model."""

    logger.info("Starting maintenance model training example")

    # Create database session
    db = SessionLocal()

    try:
        # Get vehicle IDs for training
        # In production, query actual vehicles from database
        vehicle_ids = [f"V{str(i).zfill(3)}" for i in range(1, 101)]  # V001-V100

        logger.info(f"Training on {len(vehicle_ids)} vehicles")

        # Generate labels
        # In production, derive from actual maintenance records
        labels = generate_sample_labels(vehicle_ids, db)

        # Create training pipeline
        pipeline = TrainingPipeline(db, model_storage_path="./models")

        # Train model
        job = pipeline.train_model(
            model_name="maintenance_predictor",
            entity_type="Vehicle",
            entity_ids=vehicle_ids,
            labels=labels,
            test_size=0.2,
            random_state=42,
            hyperparameters={
                "n_estimators": 100,
                "max_depth": 10,
            },
        )

        # Print results
        logger.info(f"Training job status: {job.status}")
        logger.info(f"Metrics: {job.metrics}")

        if job.status == "completed":
            logger.info("✓ Model training successful!")
            logger.info(f"  - Validation accuracy: {job.metrics.get('val_accuracy', 'N/A')}")
            logger.info(f"  - Validation F1 score: {job.metrics.get('val_f1', 'N/A')}")
            logger.info(f"  - Validation AUC: {job.metrics.get('val_auc', 'N/A')}")
        else:
            logger.error(f"✗ Model training failed: {job.error}")

    except Exception as e:
        logger.error(f"Training failed: {e}", exc_info=True)

    finally:
        db.close()


if __name__ == "__main__":
    main()
