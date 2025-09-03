"""
Prediction routes for the ML service.

Handles passenger survival prediction requests.
"""

from fastapi import APIRouter, Request, Depends
from typing import Dict, Any
import time

from app.models.requests import PassengerData
from app.models.responses import PredictionResponse
from app.api.middleware.auth import get_current_user
from app.utils.validation import validate_passenger_input
from app.services.lazy_ml_service import fast_ml_service as ml_service
from app.core.exceptions import (
    MLServiceError,
    ValidationError,
    PredictionError,
    PredictionInputError,
    ModelUnavailableError,
    ModelNotLoadedError,
)
from app.core.logging_config import get_logger

router = APIRouter(tags=["Predictions"])
logger = get_logger("prediction_routes")


@router.post(
    "/predict",
    response_model=PredictionResponse,
    responses={
        200: {
            "description": "Successful prediction",
            "content": {
                "application/json": {
                    "examples": {
                        "high_survival": {
                            "summary": "High survival probability",
                            "value": {
                                "prediction": 1,
                                "probability": 0.9234,
                                "confidence": "high",
                                "model_version": "2.1.0",
                                "request_id": "abc12345",
                            },
                        },
                        "low_survival": {
                            "summary": "Low survival probability",
                            "value": {
                                "prediction": 0,
                                "probability": 0.1456,
                                "confidence": "medium",
                                "model_version": "2.1.0",
                                "request_id": "def67890",
                            },
                        },
                    }
                }
            },
        },
        400: {
            "description": "Invalid input data",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "PREDICTION_INPUT_ERROR",
                        "message": "Invalid input data: age must be between 0 and 120",
                        "details": {
                            "field_errors": {"age": ["Must be between 0 and 120"]}
                        },
                        "request_id": "req_123",
                        "timestamp": "2025-09-02T15:36:30.030Z",
                    }
                }
            },
        },
        401: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "AUTHENTICATION_ERROR",
                        "message": "Token has expired",
                        "request_id": "req_124",
                        "timestamp": "2025-09-02T15:36:30.030Z",
                    }
                }
            },
        },
        503: {
            "description": "Models temporarily unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "error_code": "MODEL_UNAVAILABLE",
                        "message": "ML models are temporarily unavailable",
                        "request_id": "req_125",
                        "timestamp": "2025-09-02T15:36:30.030Z",
                    }
                }
            },
        },
    },
)
async def predict_survival(
    request: Request,
    passenger: PassengerData,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    **Predict passenger survival using ML models**

    This endpoint uses dual ML models (Logistic Regression + Decision Tree) to predict
    whether a Titanic passenger would survive based on their characteristics.

    **Firebase Optimization:**
    - Models are lazy-loaded on first prediction request (~1-2s)
    - Subsequent requests in the same container use cached models (~50-100ms)
    - Ultra-fast cold start with deferred model loading

    **Authentication:**
    - Requires valid JWT Bearer token
    - Rate limited to 100 requests/minute per user

    **Input Validation:**
    - XSS and SQL injection prevention
    - Statistical outlier detection
    - Comprehensive field validation

    **Response:**
    - `prediction`: 0 (did not survive) or 1 (survived)
    - `probability`: Confidence score (0.0 - 1.0)
    - `confidence`: "low", "medium", or "high" based on model agreement
    - `model_version`: API version for tracking
    - `request_id`: Unique identifier for request tracing

    **Performance:**
    - First request: ~1-2 seconds (includes model loading)
    - Warm requests: ~50-100ms (cached models)
    - Memory efficient with lazy loading
    """
    try:
        request_id = getattr(request.state, "request_id", None)

        # Fast input validation
        passenger_data = passenger.model_dump()
        sanitized_data = validate_passenger_input(passenger_data)

        # Make prediction (models loaded on first call)
        prediction_start = time.time()
        prediction = await ml_service.predict_survival(sanitized_data)
        prediction_time = (time.time() - prediction_start) * 1000

        # Log only if slow or first request
        if prediction_time > 200:
            logger.info(
                "Prediction completed",
                request_id=request_id,
                user_id=current_user["user_id"],
                duration_ms=round(prediction_time, 2),
                models_lazy_loaded=(prediction_time > 1000),
            )

        return prediction

    except (
        MLServiceError,
        ValidationError,
        PredictionError,
        PredictionInputError,
        ModelUnavailableError,
        ModelNotLoadedError,
    ):
        # Re-raise specific ML service exceptions as-is
        raise
    except ValueError as e:
        # Input validation errors
        request_id = getattr(request.state, "request_id", None)
        logger.warning(f"Invalid input data: {str(e)}", request_id=request_id)
        raise PredictionInputError(f"Invalid input data: {str(e)}")
    except Exception as e:
        # Unexpected system errors
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"Prediction failed: {str(e)}", request_id=request_id)
        raise PredictionError(f"Prediction failed: {str(e)}")
