"""
Model information routes for the ML service.

Provides endpoints for retrieving model metadata and configuration.
"""

from fastapi import APIRouter, HTTPException, Request
from app.services.lazy_ml_service import fast_ml_service as ml_service
from app.core.logging_config import get_logger

router = APIRouter(tags=["Models"])
logger = get_logger("model_routes")


@router.get("/models/info")
async def model_info(request: Request):
    """Fast model info without loading models."""
    try:
        return {
            "models_loaded": ml_service.is_loaded,
            "feature_columns": ml_service.get_feature_columns(),
            "model_accuracy": ml_service.model_accuracy,
            "model_types": ["logistic_regression", "decision_tree", "ensemble"],
            "loading_mode": "lazy",
        }
    except Exception as e:
        logger.error(f"Model info failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Model info unavailable")
