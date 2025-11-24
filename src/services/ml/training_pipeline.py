"""Training Pipeline - Orchestrate ML model training.

Coordinates feature engineering, model training, evaluation, and deployment.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from uuid import uuid4
import numpy as np
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from .feature_engineering import FeatureEngineering, FeatureVector
from .model_base import (
    BaseMLModel,
    ModelMetadata,
    ModelStatus,
    ModelType,
    get_model_registry,
)
from ...config import get_logger

logger = get_logger(__name__)


class TrainingJob:
    """Represents a model training job."""

    def __init__(
        self,
        job_id: str,
        model_name: str,
        entity_type: str,
        entity_ids: List[str],
    ):
        self.job_id = job_id
        self.model_name = model_name
        self.entity_type = entity_type
        self.entity_ids = entity_ids
        self.status = "pending"
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.metrics: Dict[str, float] = {}
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "job_id": self.job_id,
            "model_name": self.model_name,
            "entity_type": self.entity_type,
            "entity_count": len(self.entity_ids),
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "metrics": self.metrics,
            "error": self.error,
        }


class TrainingPipeline:
    """Pipeline for training ML models.

    Example:
        >>> pipeline = TrainingPipeline(db)
        >>>
        >>> # Train maintenance prediction model
        >>> job = pipeline.train_model(
        ...     model_name="maintenance_predictor",
        ...     entity_type="Vehicle",
        ...     entity_ids=["V001", "V002", "V003"],
        ...     labels=[1, 0, 1],  # 1=needs maintenance, 0=ok
        ... )
        >>> print(f"Training job: {job.job_id}")
        >>> print(f"Metrics: {job.metrics}")
    """

    def __init__(self, db: Session, model_storage_path: str = "./models"):
        self.db = db
        self.model_storage_path = model_storage_path
        self.feature_engineering = FeatureEngineering(db)
        self.registry = get_model_registry()

    def train_model(
        self,
        model_name: str,
        entity_type: str,
        entity_ids: List[str],
        labels: List[Any],
        test_size: float = 0.2,
        random_state: int = 42,
        hyperparameters: Optional[Dict[str, Any]] = None,
    ) -> TrainingJob:
        """Train a model.

        Args:
            model_name: Name of registered model
            entity_type: Type of entity (Vehicle, WorkOrder, Part)
            entity_ids: List of entity IDs for training
            labels: Labels for supervised learning
            test_size: Fraction of data for testing
            random_state: Random seed
            hyperparameters: Optional model hyperparameters

        Returns:
            TrainingJob with results
        """
        job = TrainingJob(
            job_id=str(uuid4()),
            model_name=model_name,
            entity_type=entity_type,
            entity_ids=entity_ids,
        )

        try:
            job.status = "running"
            job.started_at = datetime.utcnow()

            logger.info(
                f"Starting training job {job.job_id} for {model_name} "
                f"with {len(entity_ids)} samples"
            )

            # Step 1: Extract features
            logger.info("Extracting features...")
            feature_vectors = self.feature_engineering.extract_batch_features(
                entity_type, entity_ids
            )

            if len(feature_vectors) != len(labels):
                raise ValueError(
                    f"Feature count ({len(feature_vectors)}) does not match "
                    f"label count ({len(labels)})"
                )

            # Convert to numpy arrays
            X = np.array([fv.to_array() for fv in feature_vectors])
            y = np.array(labels)
            feature_names = feature_vectors[0].feature_names if feature_vectors else []

            logger.info(f"Features shape: {X.shape}, Labels shape: {y.shape}")

            # Step 2: Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state
            )

            logger.info(
                f"Train size: {len(X_train)}, Test size: {len(X_test)}"
            )

            # Step 3: Create model
            model_class = self.registry.get(model_name)
            if not model_class:
                raise ValueError(f"Model {model_name} not registered")

            metadata = ModelMetadata(
                model_id=str(uuid4()),
                model_name=model_name,
                model_type=ModelType.CLASSIFICATION,  # Default, can be customized
                version="1.0",
                created_at=datetime.utcnow(),
                status=ModelStatus.TRAINING,
            )
            metadata.feature_names = feature_names
            metadata.hyperparameters = hyperparameters or {}

            model = model_class(metadata)

            # Step 4: Train model
            logger.info("Training model...")
            training_metrics = model.train(
                X_train, y_train, validation_data=(X_test, y_test)
            )

            # Step 5: Evaluate model
            logger.info("Evaluating model...")
            eval_metrics = model.evaluate(X_test, y_test)

            # Combine metrics
            job.metrics = {**training_metrics, **eval_metrics}
            model.metadata.metrics = job.metrics
            model.metadata.status = ModelStatus.TRAINED

            # Step 6: Save model
            model_path = f"{self.model_storage_path}/{model_name}_{metadata.model_id}.pkl"
            model.save(model_path)

            logger.info(f"Model saved to {model_path}")

            # Mark job complete
            job.status = "completed"
            job.completed_at = datetime.utcnow()

            logger.info(
                f"Training job {job.job_id} completed successfully. "
                f"Metrics: {job.metrics}"
            )

        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.utcnow()
            logger.error(f"Training job {job.job_id} failed: {e}", exc_info=True)

        return job

    def evaluate_model(
        self,
        model: BaseMLModel,
        entity_type: str,
        entity_ids: List[str],
        labels: List[Any],
    ) -> Dict[str, float]:
        """Evaluate a trained model on new data.

        Args:
            model: Trained model
            entity_type: Type of entity
            entity_ids: List of entity IDs
            labels: True labels

        Returns:
            Dictionary with evaluation metrics
        """
        # Extract features
        feature_vectors = self.feature_engineering.extract_batch_features(
            entity_type, entity_ids
        )

        if len(feature_vectors) != len(labels):
            raise ValueError("Feature count does not match label count")

        # Convert to arrays
        X = np.array([fv.to_array() for fv in feature_vectors])
        y = np.array(labels)

        # Evaluate
        metrics = model.evaluate(X, y)

        logger.info(f"Evaluation metrics: {metrics}")

        return metrics

    def create_training_dataset(
        self,
        entity_type: str,
        entity_ids: List[str],
        label_extractor: callable,
    ) -> Tuple[List[FeatureVector], List[Any]]:
        """Create training dataset with automatic label extraction.

        Args:
            entity_type: Type of entity
            entity_ids: List of entity IDs
            label_extractor: Function that takes entity_id and returns label

        Returns:
            Tuple of (feature_vectors, labels)
        """
        feature_vectors = self.feature_engineering.extract_batch_features(
            entity_type, entity_ids
        )

        labels = []
        for entity_id in entity_ids:
            try:
                label = label_extractor(entity_id)
                labels.append(label)
            except Exception as e:
                logger.error(
                    f"Failed to extract label for {entity_id}: {e}"
                )
                labels.append(None)

        # Filter out None labels
        valid_pairs = [
            (fv, label)
            for fv, label in zip(feature_vectors, labels)
            if label is not None
        ]

        if not valid_pairs:
            return [], []

        valid_features, valid_labels = zip(*valid_pairs)

        logger.info(
            f"Created dataset with {len(valid_features)} samples "
            f"({len(entity_ids) - len(valid_features)} skipped)"
        )

        return list(valid_features), list(valid_labels)
