"""
API routes for the Titanic ML Service.

Organized into logical groups:
- health: Service health monitoring
- predictions: ML predictions
- models: Model information
"""

from .health import router as health_router
from .predictions import router as predictions_router
from .models import router as models_router

__all__ = ["health_router", "predictions_router", "models_router"]
