"""ML API Endpoints - Machine Learning predictions (WP20).

Provides HTTP endpoints for ML predictions and model management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from ....models.database import get_db
from ....models.railfleet.ml_models import MLModel, MLPrediction
from ....services.ml.feature_engineering import FeatureEngineering
from ....services.ml.prediction_service import PredictionService
from ....config import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class FeatureExtractionRequest(BaseModel):
    """Request to extract features."""

    entity_type: str = Field(..., description="Vehicle, WorkOrder, or Part")
    entity_ids: List[str] = Field(..., description="List of entity IDs")


class PredictionRequest(BaseModel):
    """Request for predictions."""

    model_name: str = Field(..., description="Name of model to use")
    entity_type: str = Field(..., description="Vehicle, WorkOrder, or Part")
    entity_ids: List[str] = Field(..., description="List of entity IDs")


# ============================================================================
# Feature Engineering Endpoints
# ============================================================================


@router.post("/ml/features/extract")
def extract_features(
    request: FeatureExtractionRequest,
    db: Session = Depends(get_db),
):
    """Extract ML features for entities.

    Args:
        request: Feature extraction request
        db: Database session

    Returns:
        Feature vectors for entities
    """
    fe = FeatureEngineering(db)

    feature_vectors = fe.extract_batch_features(
        request.entity_type, request.entity_ids
    )

    return {
        "entity_type": request.entity_type,
        "features": [fv.to_dict() for fv in feature_vectors],
        "count": len(feature_vectors),
    }


@router.get("/ml/features/{entity_type}/{entity_id}")
def get_entity_features(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db),
):
    """Get features for a single entity.

    Args:
        entity_type: Type of entity
        entity_id: Entity identifier
        db: Database session

    Returns:
        Feature vector
    """
    fe = FeatureEngineering(db)

    if entity_type == "Vehicle":
        fv = fe.extract_vehicle_features(entity_id)
    elif entity_type == "WorkOrder":
        fv = fe.extract_workorder_features(entity_id)
    elif entity_type == "Part":
        fv = fe.extract_inventory_features(entity_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown entity type: {entity_type}",
        )

    return fv.to_dict()


# ============================================================================
# Model Management Endpoints
# ============================================================================


@router.get("/ml/models")
def list_models(
    db: Session = Depends(get_db),
):
    """List all ML models.

    Args:
        db: Database session

    Returns:
        List of models
    """
    models = db.query(MLModel).order_by(MLModel.created_at.desc()).all()

    return {
        "models": [
            {
                "model_id": m.model_id,
                "model_name": m.model_name,
                "model_type": m.model_type,
                "version": m.version,
                "status": m.status,
                "created_at": m.created_at,
                "metrics": m.metrics,
            }
            for m in models
        ],
        "count": len(models),
    }


@router.get("/ml/models/{model_id}")
def get_model(
    model_id: str,
    db: Session = Depends(get_db),
):
    """Get model details.

    Args:
        model_id: Model identifier
        db: Database session

    Returns:
        Model details
    """
    model = db.query(MLModel).filter(MLModel.model_id == model_id).first()

    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found",
        )

    return {
        "model_id": model.model_id,
        "model_name": model.model_name,
        "model_type": model.model_type,
        "version": model.version,
        "status": model.status,
        "feature_names": model.feature_names,
        "hyperparameters": model.hyperparameters,
        "metrics": model.metrics,
        "created_at": model.created_at,
        "trained_at": model.trained_at,
        "deployed_at": model.deployed_at,
        "file_path": model.file_path,
    }


# ============================================================================
# Prediction Endpoints
# ============================================================================


@router.get("/ml/predictions/history/{entity_type}/{entity_id}")
def get_prediction_history(
    entity_type: str,
    entity_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Get prediction history for an entity.

    Args:
        entity_type: Type of entity
        entity_id: Entity identifier
        limit: Maximum predictions to return
        db: Database session

    Returns:
        Prediction history
    """
    predictions = (
        db.query(MLPrediction)
        .filter(
            MLPrediction.entity_type == entity_type,
            MLPrediction.entity_id == entity_id,
        )
        .order_by(MLPrediction.predicted_at.desc())
        .limit(limit)
        .all()
    )

    return {
        "entity_type": entity_type,
        "entity_id": entity_id,
        "predictions": [
            {
                "prediction_id": p.prediction_id,
                "model_name": p.model_name,
                "prediction_value": p.prediction_value,
                "confidence": p.confidence,
                "probabilities": p.probabilities,
                "predicted_at": p.predicted_at,
            }
            for p in predictions
        ],
        "count": len(predictions),
    }


@router.get("/ml/predictions/stats")
def get_prediction_stats(
    db: Session = Depends(get_db),
):
    """Get prediction statistics.

    Args:
        db: Database session

    Returns:
        Prediction statistics
    """
    from sqlalchemy import func

    # Count by model
    model_counts = (
        db.query(
            MLPrediction.model_name,
            func.count(MLPrediction.id).label("count"),
        )
        .group_by(MLPrediction.model_name)
        .all()
    )

    # Count by entity type
    entity_counts = (
        db.query(
            MLPrediction.entity_type,
            func.count(MLPrediction.id).label("count"),
        )
        .group_by(MLPrediction.entity_type)
        .all()
    )

    # Total predictions
    total = db.query(func.count(MLPrediction.id)).scalar()

    return {
        "total_predictions": total,
        "by_model": {name: count for name, count in model_counts},
        "by_entity_type": {entity_type: count for entity_type, count in entity_counts},
    }
