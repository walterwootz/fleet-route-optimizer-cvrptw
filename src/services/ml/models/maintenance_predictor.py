"""Maintenance Predictor - Predict vehicle maintenance needs.

Uses historical maintenance patterns to predict when vehicles need maintenance.
"""

import numpy as np
from typing import Dict, List, Optional, Any
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

from ..model_base import BaseMLModel, Prediction, register_model
from ....config import get_logger

logger = get_logger(__name__)


@register_model("maintenance_predictor")
class MaintenancePredictor(BaseMLModel):
    """Predicts whether a vehicle needs maintenance soon.

    Features used:
    - age_days: Vehicle age in days
    - mileage: Current mileage
    - event_count: Total events
    - maintenance_count_total: Total maintenance events
    - maintenance_count_90d: Recent maintenance (90 days)
    - days_since_maintenance: Days since last maintenance
    - avg_days_between_maintenance: Average maintenance interval
    - critical_event_count_30d: Recent critical events
    - status_duration_days: Days in current status

    Target:
    - 1 = Needs maintenance soon (within 30 days)
    - 0 = OK for now

    Example:
        >>> model = MaintenancePredictor(metadata)
        >>> metrics = model.train(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(self, metadata):
        super().__init__(metadata)
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            **metadata.hyperparameters
        )

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_data: Optional[tuple] = None,
    ) -> Dict[str, float]:
        """Train maintenance prediction model.

        Args:
            X: Training features (n_samples, n_features)
            y: Training labels (1=needs maintenance, 0=ok)
            validation_data: Optional (X_val, y_val)

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training maintenance predictor on {len(X)} samples")

        # Train model
        self.model.fit(X, y)

        # Calculate training metrics
        y_train_pred = self.model.predict(X)
        y_train_proba = self.model.predict_proba(X)[:, 1]

        train_metrics = {
            "train_accuracy": float(accuracy_score(y, y_train_pred)),
            "train_precision": float(precision_score(y, y_train_pred, zero_division=0)),
            "train_recall": float(recall_score(y, y_train_pred, zero_division=0)),
            "train_f1": float(f1_score(y, y_train_pred, zero_division=0)),
            "train_auc": float(roc_auc_score(y, y_train_proba)),
        }

        # Validation metrics if provided
        if validation_data:
            X_val, y_val = validation_data
            y_val_pred = self.model.predict(X_val)
            y_val_proba = self.model.predict_proba(X_val)[:, 1]

            val_metrics = {
                "val_accuracy": float(accuracy_score(y_val, y_val_pred)),
                "val_precision": float(precision_score(y_val, y_val_pred, zero_division=0)),
                "val_recall": float(recall_score(y_val, y_val_pred, zero_division=0)),
                "val_f1": float(f1_score(y_val, y_val_pred, zero_division=0)),
                "val_auc": float(roc_auc_score(y_val, y_val_proba)),
            }
            train_metrics.update(val_metrics)

        logger.info(f"Training complete. Metrics: {train_metrics}")

        return train_metrics

    def predict(self, X: np.ndarray) -> List[Prediction]:
        """Predict maintenance needs for vehicles.

        Args:
            X: Feature matrix (n_samples, n_features)

        Returns:
            List of Prediction objects
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        # Get predictions and probabilities
        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)

        predictions = []
        for i, (pred, proba) in enumerate(zip(y_pred, y_proba)):
            prediction = Prediction(
                entity_id="",  # Will be set by prediction service
                prediction="needs_maintenance" if pred == 1 else "ok",
                confidence=float(max(proba)),
                probabilities={
                    "ok": float(proba[0]),
                    "needs_maintenance": float(proba[1]),
                },
                metadata={
                    "prediction_value": int(pred),
                    "risk_score": float(proba[1]),  # Probability of needing maintenance
                },
            )
            predictions.append(prediction)

        return predictions

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """Evaluate model performance.

        Args:
            X: Test features
            y: Test labels

        Returns:
            Dictionary with evaluation metrics
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        y_pred = self.model.predict(X)
        y_proba = self.model.predict_proba(X)[:, 1]

        metrics = {
            "test_accuracy": float(accuracy_score(y, y_pred)),
            "test_precision": float(precision_score(y, y_pred, zero_division=0)),
            "test_recall": float(recall_score(y, y_pred, zero_division=0)),
            "test_f1": float(f1_score(y, y_pred, zero_division=0)),
            "test_auc": float(roc_auc_score(y, y_proba)),
        }

        logger.info(f"Evaluation metrics: {metrics}")

        return metrics

    def get_maintenance_risk_threshold(self, risk_level: str = "medium") -> float:
        """Get probability threshold for maintenance risk level.

        Args:
            risk_level: "low", "medium", or "high"

        Returns:
            Probability threshold
        """
        thresholds = {
            "low": 0.3,    # Conservative - catch more potential issues
            "medium": 0.5,  # Balanced
            "high": 0.7,    # Aggressive - only flag high-confidence cases
        }
        return thresholds.get(risk_level, 0.5)

    def predict_with_risk_level(
        self, X: np.ndarray, risk_level: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Predict with custom risk threshold.

        Args:
            X: Feature matrix
            risk_level: Risk tolerance level

        Returns:
            List of predictions with risk classification
        """
        threshold = self.get_maintenance_risk_threshold(risk_level)
        y_proba = self.model.predict_proba(X)[:, 1]

        results = []
        for i, prob in enumerate(y_proba):
            result = {
                "needs_maintenance": prob >= threshold,
                "risk_score": float(prob),
                "risk_level": self._classify_risk(prob),
                "threshold_used": threshold,
            }
            results.append(result)

        return results

    def _classify_risk(self, probability: float) -> str:
        """Classify risk level based on probability.

        Args:
            probability: Maintenance probability (0-1)

        Returns:
            Risk level string
        """
        if probability >= 0.8:
            return "critical"
        elif probability >= 0.6:
            return "high"
        elif probability >= 0.4:
            return "medium"
        else:
            return "low"
