"""Prediction Service - ML model inference.

Provides prediction capabilities using trained ML models.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import numpy as np
from sqlalchemy.orm import Session

from .feature_engineering import FeatureEngineering
from .model_base import BaseMLModel, Prediction, get_model_registry
from ...config import get_logger

logger = get_logger(__name__)


class PredictionService:
    """Service for making predictions with trained models.

    Example:
        >>> service = PredictionService(db)
        >>> service.load_model("maintenance_predictor", "path/to/model.pkl")
        >>> predictions = service.predict("Vehicle", ["V001", "V002"])
        >>> for pred in predictions:
        ...     print(f"{pred.entity_id}: {pred.prediction} (conf: {pred.confidence})")
    """

    def __init__(self, db: Session):
        self.db = db
        self.feature_engineering = FeatureEngineering(db)
        self.registry = get_model_registry()
        self._loaded_models: Dict[str, BaseMLModel] = {}

    def load_model(self, model_name: str, model_path: str):
        """Load a trained model.

        Args:
            model_name: Name for the model
            model_path: Path to model file

        """
        if model_name in self._loaded_models:
            logger.info(f"Model {model_name} already loaded")
            return

        model_class = self.registry.get(model_name)
        if not model_class:
            raise ValueError(f"Model {model_name} not registered")

        # Create model instance (metadata will be loaded from file)
        from .model_base import ModelMetadata, ModelType, ModelStatus

        metadata = ModelMetadata(
            model_id="temp",
            model_name=model_name,
            model_type=ModelType.CLASSIFICATION,
            version="1.0",
            created_at=datetime.utcnow(),
            status=ModelStatus.DEPLOYED,
        )

        model = model_class(metadata)
        model.load(model_path)

        self._loaded_models[model_name] = model
        logger.info(f"Loaded model {model_name} from {model_path}")

    def predict(
        self,
        model_name: str,
        entity_type: str,
        entity_ids: List[str],
    ) -> List[Prediction]:
        """Make predictions for entities.

        Args:
            model_name: Name of loaded model
            entity_type: Type of entity
            entity_ids: List of entity IDs

        Returns:
            List of Prediction objects
        """
        if model_name not in self._loaded_models:
            raise ValueError(f"Model {model_name} not loaded")

        model = self._loaded_models[model_name]

        # Extract features
        feature_vectors = self.feature_engineering.extract_batch_features(
            entity_type, entity_ids
        )

        if not feature_vectors:
            logger.warning(f"No features extracted for {len(entity_ids)} entities")
            return []

        # Convert to numpy array
        X = np.array([fv.to_array() for fv in feature_vectors])

        # Make predictions
        predictions = model.predict(X)

        # Attach entity IDs
        for pred, fv in zip(predictions, feature_vectors):
            pred.entity_id = fv.entity_id

        logger.info(f"Made {len(predictions)} predictions with {model_name}")

        return predictions

    def predict_single(
        self,
        model_name: str,
        entity_type: str,
        entity_id: str,
    ) -> Optional[Prediction]:
        """Make prediction for single entity.

        Args:
            model_name: Name of loaded model
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            Prediction or None
        """
        predictions = self.predict(model_name, entity_type, [entity_id])
        return predictions[0] if predictions else None

    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model names.

        Returns:
            List of model names
        """
        return list(self._loaded_models.keys())

    def unload_model(self, model_name: str):
        """Unload a model from memory.

        Args:
            model_name: Name of model to unload
        """
        if model_name in self._loaded_models:
            del self._loaded_models[model_name]
            logger.info(f"Unloaded model {model_name}")
