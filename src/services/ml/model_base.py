"""ML Model Base Classes - Foundation for machine learning models.

Provides base classes, model registry, and versioning for ML models.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
from enum import Enum
import json
import pickle
from pathlib import Path

from ...config import get_logger

logger = get_logger(__name__)


class ModelType(str, Enum):
    """Type of ML model."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    ANOMALY_DETECTION = "anomaly_detection"


class ModelStatus(str, Enum):
    """Status of ML model."""

    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"
    FAILED = "failed"


class ModelMetadata:
    """Metadata for ML model."""

    def __init__(
        self,
        model_id: str,
        model_name: str,
        model_type: ModelType,
        version: str,
        created_at: datetime,
        status: ModelStatus = ModelStatus.TRAINING,
    ):
        self.model_id = model_id
        self.model_name = model_name
        self.model_type = model_type
        self.version = version
        self.created_at = created_at
        self.status = status
        self.metrics: Dict[str, float] = {}
        self.hyperparameters: Dict[str, Any] = {}
        self.feature_names: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "model_id": self.model_id,
            "model_name": self.model_name,
            "model_type": self.model_type.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
            "metrics": self.metrics,
            "hyperparameters": self.hyperparameters,
            "feature_names": self.feature_names,
        }


class Prediction:
    """Prediction result from ML model."""

    def __init__(
        self,
        entity_id: str,
        prediction: Any,
        confidence: Optional[float] = None,
        probabilities: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.entity_id = entity_id
        self.prediction = prediction
        self.confidence = confidence
        self.probabilities = probabilities or {}
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "entity_id": self.entity_id,
            "prediction": self.prediction,
            "confidence": self.confidence,
            "probabilities": self.probabilities,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseMLModel(ABC):
    """Base class for all ML models.

    Example:
        >>> class MaintenancePredictor(BaseMLModel):
        ...     def train(self, X, y):
        ...         self.model = RandomForestClassifier()
        ...         self.model.fit(X, y)
        ...
        ...     def predict(self, X):
        ...         return self.model.predict(X)
    """

    def __init__(self, metadata: ModelMetadata):
        self.metadata = metadata
        self.model: Optional[Any] = None  # Underlying ML model (sklearn, etc.)

    @abstractmethod
    def train(
        self,
        X: Any,
        y: Any,
        validation_data: Optional[tuple] = None,
    ) -> Dict[str, float]:
        """Train the model.

        Args:
            X: Training features
            y: Training labels
            validation_data: Optional (X_val, y_val)

        Returns:
            Dictionary with training metrics
        """
        pass

    @abstractmethod
    def predict(self, X: Any) -> List[Prediction]:
        """Make predictions.

        Args:
            X: Features for prediction

        Returns:
            List of Prediction objects
        """
        pass

    @abstractmethod
    def evaluate(self, X: Any, y: Any) -> Dict[str, float]:
        """Evaluate model performance.

        Args:
            X: Test features
            y: Test labels

        Returns:
            Dictionary with evaluation metrics
        """
        pass

    def save(self, path: str):
        """Save model to disk.

        Args:
            path: Path to save model
        """
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        # Save model
        with open(path_obj, "wb") as f:
            pickle.dump(self.model, f)

        # Save metadata
        metadata_path = path_obj.with_suffix(".json")
        with open(metadata_path, "w") as f:
            json.dump(self.metadata.to_dict(), f, indent=2)

        logger.info(f"Saved model {self.metadata.model_id} to {path}")

    def load(self, path: str):
        """Load model from disk.

        Args:
            path: Path to load model from
        """
        path_obj = Path(path)

        # Load model
        with open(path_obj, "rb") as f:
            self.model = pickle.load(f)

        # Load metadata
        metadata_path = path_obj.with_suffix(".json")
        if metadata_path.exists():
            with open(metadata_path, "r") as f:
                metadata_dict = json.load(f)
                # Update metadata (keeping object reference)
                self.metadata.status = ModelStatus(metadata_dict["status"])
                self.metadata.metrics = metadata_dict["metrics"]
                self.metadata.hyperparameters = metadata_dict["hyperparameters"]
                self.metadata.feature_names = metadata_dict["feature_names"]

        logger.info(f"Loaded model {self.metadata.model_id} from {path}")

    def get_feature_importance(self) -> Optional[Dict[str, float]]:
        """Get feature importance if supported by model.

        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.model is None:
            return None

        # Check if model has feature_importances_ attribute (sklearn models)
        if hasattr(self.model, "feature_importances_"):
            importances = self.model.feature_importances_
            return {
                name: float(importance)
                for name, importance in zip(
                    self.metadata.feature_names, importances
                )
            }

        return None


class ModelRegistry:
    """Registry for managing ML models.

    Example:
        >>> registry = ModelRegistry()
        >>> registry.register("maintenance_predictor", MaintenancePredictor)
        >>> model_class = registry.get("maintenance_predictor")
        >>> model = model_class(metadata)
    """

    def __init__(self):
        self._models: Dict[str, Type[BaseMLModel]] = {}

    def register(self, name: str, model_class: Type[BaseMLModel]):
        """Register a model class.

        Args:
            name: Model name for lookup
            model_class: Model class (subclass of BaseMLModel)
        """
        if not issubclass(model_class, BaseMLModel):
            raise ValueError(
                f"Model class must be subclass of BaseMLModel, got {model_class}"
            )

        self._models[name] = model_class
        logger.info(f"Registered model: {name}")

    def get(self, name: str) -> Optional[Type[BaseMLModel]]:
        """Get a registered model class.

        Args:
            name: Model name

        Returns:
            Model class or None if not found
        """
        return self._models.get(name)

    def list_models(self) -> List[str]:
        """List all registered models.

        Returns:
            List of model names
        """
        return list(self._models.keys())

    def unregister(self, name: str):
        """Unregister a model.

        Args:
            name: Model name
        """
        if name in self._models:
            del self._models[name]
            logger.info(f"Unregistered model: {name}")


# Global model registry
_registry = ModelRegistry()


def get_model_registry() -> ModelRegistry:
    """Get global model registry.

    Returns:
        ModelRegistry instance
    """
    return _registry


def register_model(name: str):
    """Decorator to register a model class.

    Example:
        >>> @register_model("maintenance_predictor")
        ... class MaintenancePredictor(BaseMLModel):
        ...     pass
    """

    def decorator(model_class: Type[BaseMLModel]):
        _registry.register(name, model_class)
        return model_class

    return decorator
