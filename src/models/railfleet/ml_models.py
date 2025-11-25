"""Database models for ML model metadata and predictions."""

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Float, Boolean, text
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base


class MLModel(Base):
    """ML model metadata table."""

    __tablename__ = "ml_models"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Model identification
    model_id = Column(String, nullable=False, unique=True, index=True)
    model_name = Column(String, nullable=False, index=True)
    model_type = Column(String, nullable=False)  # classification, regression, etc.
    version = Column(String, nullable=False)

    # Model status
    status = Column(String, nullable=False, default="training", index=True)

    # Model artifacts
    file_path = Column(String, nullable=True)  # Path to saved model
    feature_names = Column(JSONB, nullable=False, default=list)

    # Hyperparameters and configuration
    hyperparameters = Column(JSONB, nullable=False, default=dict)

    # Performance metrics
    metrics = Column(JSONB, nullable=False, default=dict)

    # Timestamps
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True
    )
    trained_at = Column(DateTime, nullable=True)
    deployed_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<MLModel {self.model_name} v{self.version} ({self.status})>"


class MLPrediction(Base):
    """ML prediction history table."""

    __tablename__ = "ml_predictions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Prediction identification
    prediction_id = Column(String, nullable=False, unique=True, index=True)

    # Model used
    model_id = Column(String, nullable=False, index=True)
    model_name = Column(String, nullable=False, index=True)

    # Entity predicted
    entity_type = Column(String, nullable=False, index=True)
    entity_id = Column(String, nullable=False, index=True)

    # Prediction results
    prediction_value = Column(String, nullable=False)
    confidence = Column(Float, nullable=True)
    probabilities = Column(JSONB, nullable=False, default=dict)

    # Feature values used
    features = Column(JSONB, nullable=False, default=dict)

    # Metadata
    metadata = Column(JSONB, nullable=False, default=dict)

    # Timestamp
    predicted_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
        index=True
    )

    def __repr__(self):
        return f"<MLPrediction {self.entity_type}:{self.entity_id} = {self.prediction_value}>"
