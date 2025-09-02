"""
Data models for the Titanic ML Service.

Organized into:
- requests: Input validation models
- responses: Output/response models
"""

from .requests import PassengerData
from .responses import (
    ModelPrediction,
    EnsemblePrediction,
    PredictionResponse,
    HealthResponse,
    ErrorResponse
)

__all__ = [
    'PassengerData',
    'ModelPrediction',
    'EnsemblePrediction',
    'PredictionResponse',
    'HealthResponse',
    'ErrorResponse'
]