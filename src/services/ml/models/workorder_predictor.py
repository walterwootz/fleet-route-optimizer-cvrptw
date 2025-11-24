"""Work Order Predictor - Predict work order completion time and delays.

Predicts whether work orders will be completed on time or delayed.
"""

import numpy as np
from typing import Dict, List, Optional
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ..model_base import BaseMLModel, Prediction, register_model
from ....config import get_logger

logger = get_logger(__name__)


@register_model("workorder_completion_predictor")
class WorkOrderCompletionPredictor(BaseMLModel):
    """Predicts work order completion time in days.

    Features used:
    - priority_numeric: Priority level (1-4)
    - task_count: Number of tasks
    - assigned_staff_count: Number of assigned staff
    - days_since_created: Age of work order
    - days_since_started: Days since work started
    - parts_required_count: Number of parts needed
    - estimated_hours: Estimated work hours
    - status_changes_count: Number of status changes

    Target:
    - completion_days: Days until completion (regression)

    Example:
        >>> model = WorkOrderCompletionPredictor(metadata)
        >>> metrics = model.train(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(self, metadata):
        super().__init__(metadata)
        self.model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            min_samples_split=5,
            random_state=42,
            **metadata.hyperparameters
        )

    def train(
        self,
        X: np.ndarray,
        y: np.ndarray,
        validation_data: Optional[tuple] = None,
    ) -> Dict[str, float]:
        """Train work order completion predictor.

        Args:
            X: Training features
            y: Training labels (days until completion)
            validation_data: Optional (X_val, y_val)

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training work order predictor on {len(X)} samples")

        # Train model
        self.model.fit(X, y)

        # Training metrics
        y_train_pred = self.model.predict(X)
        train_metrics = {
            "train_mae": float(mean_absolute_error(y, y_train_pred)),
            "train_rmse": float(np.sqrt(mean_squared_error(y, y_train_pred))),
            "train_r2": float(r2_score(y, y_train_pred)),
        }

        # Validation metrics
        if validation_data:
            X_val, y_val = validation_data
            y_val_pred = self.model.predict(X_val)

            val_metrics = {
                "val_mae": float(mean_absolute_error(y_val, y_val_pred)),
                "val_rmse": float(np.sqrt(mean_squared_error(y_val, y_val_pred))),
                "val_r2": float(r2_score(y_val, y_val_pred)),
            }
            train_metrics.update(val_metrics)

        logger.info(f"Training complete. Metrics: {train_metrics}")

        return train_metrics

    def predict(self, X: np.ndarray) -> List[Prediction]:
        """Predict work order completion time.

        Args:
            X: Feature matrix

        Returns:
            List of Prediction objects
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        y_pred = self.model.predict(X)

        predictions = []
        for i, days in enumerate(y_pred):
            # Classify as on-time or delayed (assume 7 days is target)
            target_days = 7.0
            delay_days = max(0, days - target_days)
            is_delayed = days > target_days

            prediction = Prediction(
                entity_id="",
                prediction=f"{days:.1f} days",
                confidence=None,  # Regression doesn't have probability
                probabilities={},
                metadata={
                    "completion_days": float(days),
                    "is_delayed": bool(is_delayed),
                    "delay_days": float(delay_days),
                    "status": "delayed" if is_delayed else "on_time",
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

        metrics = {
            "test_mae": float(mean_absolute_error(y, y_pred)),
            "test_rmse": float(np.sqrt(mean_squared_error(y, y_pred))),
            "test_r2": float(r2_score(y, y_pred)),
            "test_mean_prediction": float(np.mean(y_pred)),
            "test_mean_actual": float(np.mean(y)),
        }

        logger.info(f"Evaluation metrics: {metrics}")

        return metrics
