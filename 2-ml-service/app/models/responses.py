"""
Response models for FastAPI endpoint responses.

These models define the structure of API responses, ensuring consistent
and well-documented output formats.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict


class ModelPrediction(BaseModel):
    """Individual model prediction result."""
    
    probability: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Survival probability (0.0 to 1.0)"
    )
    
    prediction: str = Field(
        ..., 
        pattern="^(survived|did_not_survive)$", 
        description="Binary prediction result"
    )


class EnsemblePrediction(BaseModel):
    """Ensemble model prediction with confidence metrics."""
    
    probability: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Ensemble survival probability (0.0 to 1.0)"
    )
    
    prediction: str = Field(
        ..., 
        pattern="^(survived|did_not_survive)$", 
        description="Ensemble binary prediction result"
    )
    
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="Confidence score (0.0 to 1.0)"
    )
    
    confidence_level: str = Field(
        ..., 
        pattern="^(low|medium|high)$", 
        description="Human-readable confidence level"
    )


class PredictionResponse(BaseModel):
    """Complete prediction response with individual and ensemble results."""
    
    individual_models: Dict[str, ModelPrediction] = Field(
        ..., 
        description="Individual model predictions"
    )
    
    ensemble_result: EnsemblePrediction = Field(
        ..., 
        description="Ensemble prediction with confidence metrics"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "individual_models": {
                    "logistic_regression": {
                        "probability": 0.888,
                        "prediction": "survived"
                    },
                    "decision_tree": {
                        "probability": 1.000,
                        "prediction": "survived"
                    }
                },
                "ensemble_result": {
                    "probability": 0.944,
                    "prediction": "survived",
                    "confidence": 0.888,
                    "confidence_level": "high"
                }
            }
        }
    )


class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service health status")
    models_loaded: bool = Field(..., description="Whether ML models are loaded")
    preprocessor_ready: bool = Field(..., description="Whether preprocessor is ready")
    
    model_accuracy: Dict[str, float] = Field(
        None, 
        description="Model accuracy metrics from training"
    )

    model_config = ConfigDict(
        protected_namespaces=(),  # Disable protected namespaces to allow 'model_' fields
        json_schema_extra={
            "example": {
                "status": "healthy",
                "models_loaded": True,
                "preprocessor_ready": True,
                "model_accuracy": {
                    "logistic_regression": 0.832,
                    "decision_tree": 0.802,
                    "ensemble": 0.817
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """Error response model for API errors."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: Dict = Field(None, description="Additional error details")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "ValidationError",
                "message": "Invalid passenger data provided",
                "details": {
                    "field": "age",
                    "issue": "Age must be between 0 and 120"
                }
            }
        }
    )