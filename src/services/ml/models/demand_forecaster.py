"""Demand Forecaster - Predict inventory part demand.

Forecasts future demand for inventory parts based on historical usage patterns.
"""

import numpy as np
from typing import Dict, List, Optional
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ..model_base import BaseMLModel, Prediction, register_model
from ....config import get_logger

logger = get_logger(__name__)


@register_model("demand_forecaster")
class DemandForecaster(BaseMLModel):
    """Forecasts part demand for next 30 days.

    Features used:
    - avg_usage_30d: Average usage (last 30 days)
    - usage_variance: Usage variance
    - moves_count_90d: Stock moves (last 90 days)
    - days_since_usage: Days since last used
    - day_of_week: Day of week (0-6)
    - month: Month (1-12)

    Target:
    - demand_next_30d: Expected demand in next 30 days (regression)

    Example:
        >>> model = DemandForecaster(metadata)
        >>> metrics = model.train(X_train, y_train)
        >>> predictions = model.predict(X_test)
    """

    def __init__(self, metadata):
        super().__init__(metadata)
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=8,
            min_samples_split=3,
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
        """Train demand forecasting model.

        Args:
            X: Training features
            y: Training labels (demand quantities)
            validation_data: Optional (X_val, y_val)

        Returns:
            Dictionary with training metrics
        """
        logger.info(f"Training demand forecaster on {len(X)} samples")

        # Train model
        self.model.fit(X, y)

        # Training metrics
        y_train_pred = self.model.predict(X)
        train_metrics = {
            "train_mae": float(mean_absolute_error(y, y_train_pred)),
            "train_rmse": float(np.sqrt(mean_squared_error(y, y_train_pred))),
            "train_r2": float(r2_score(y, y_train_pred)),
            "train_mean_demand": float(np.mean(y)),
        }

        # Validation metrics
        if validation_data:
            X_val, y_val = validation_data
            y_val_pred = self.model.predict(X_val)

            val_metrics = {
                "val_mae": float(mean_absolute_error(y_val, y_val_pred)),
                "val_rmse": float(np.sqrt(mean_squared_error(y_val, y_val_pred))),
                "val_r2": float(r2_score(y_val, y_val_pred)),
                "val_mean_demand": float(np.mean(y_val)),
            }
            train_metrics.update(val_metrics)

        logger.info(f"Training complete. Metrics: {train_metrics}")

        return train_metrics

    def predict(self, X: np.ndarray) -> List[Prediction]:
        """Predict part demand for next 30 days.

        Args:
            X: Feature matrix

        Returns:
            List of Prediction objects
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        y_pred = self.model.predict(X)

        predictions = []
        for i, demand in enumerate(y_pred):
            # Ensure non-negative demand
            demand = max(0, demand)

            # Classify urgency
            urgency = self._classify_urgency(demand)

            prediction = Prediction(
                entity_id="",
                prediction=f"{int(demand)} units",
                confidence=None,  # Regression doesn't have probability
                probabilities={},
                metadata={
                    "demand_quantity": float(demand),
                    "demand_rounded": int(np.round(demand)),
                    "urgency": urgency,
                    "reorder_recommended": urgency in ["high", "critical"],
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

        # Calculate additional metrics
        mape = np.mean(np.abs((y - y_pred) / np.maximum(y, 1))) * 100  # Avoid division by zero

        metrics = {
            "test_mae": float(mean_absolute_error(y, y_pred)),
            "test_rmse": float(np.sqrt(mean_squared_error(y, y_pred))),
            "test_r2": float(r2_score(y, y_pred)),
            "test_mape": float(mape),  # Mean Absolute Percentage Error
            "test_mean_prediction": float(np.mean(y_pred)),
            "test_mean_actual": float(np.mean(y)),
        }

        logger.info(f"Evaluation metrics: {metrics}")

        return metrics

    def _classify_urgency(self, demand: float) -> str:
        """Classify demand urgency.

        Args:
            demand: Predicted demand quantity

        Returns:
            Urgency level string
        """
        if demand >= 50:
            return "critical"
        elif demand >= 20:
            return "high"
        elif demand >= 10:
            return "medium"
        else:
            return "low"

    def forecast_with_confidence_interval(
        self, X: np.ndarray, confidence: float = 0.95
    ) -> List[Dict[str, float]]:
        """Predict with confidence intervals (for RandomForest).

        Args:
            X: Feature matrix
            confidence: Confidence level (default 0.95)

        Returns:
            List of forecasts with intervals
        """
        if self.model is None:
            raise ValueError("Model not trained")

        # Get predictions from all trees
        tree_predictions = np.array([tree.predict(X) for tree in self.model.estimators_])

        # Calculate mean and percentiles
        mean_pred = np.mean(tree_predictions, axis=0)
        lower_percentile = (1 - confidence) / 2 * 100
        upper_percentile = (1 + confidence) / 2 * 100

        lower = np.percentile(tree_predictions, lower_percentile, axis=0)
        upper = np.percentile(tree_predictions, upper_percentile, axis=0)

        forecasts = []
        for i in range(len(X)):
            forecast = {
                "demand": float(mean_pred[i]),
                "lower_bound": float(max(0, lower[i])),
                "upper_bound": float(upper[i]),
                "confidence_level": confidence,
            }
            forecasts.append(forecast)

        return forecasts
