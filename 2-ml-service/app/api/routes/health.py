"""
Health check routes for the ML service.

Provides endpoints for monitoring service health and readiness.
"""

from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
from app.models.responses import HealthResponse
from app.services.lazy_ml_service import fast_ml_service as ml_service
from app.services.health_checker import health_checker
from app.core.logging_config import get_logger

router = APIRouter(tags=["Health"])
logger = get_logger("health_routes")


@router.get("/health")
async def health_check(request: Request, detailed: Optional[str] = Query(None)):
    """
    Health check endpoint with optional detailed diagnostics.

    Args:
        detailed: If 'true', returns detailed health check with all diagnostics

    Returns basic health status by default (lazy loading).
    For detailed checks, returns comprehensive diagnostics.
    """
    try:
        if detailed and detailed.lower() == "true":
            # Detailed health check with full diagnostics
            health_data = await health_checker.run_all_checks()
            return health_data
        else:
            # Quick health check without loading models
            health_data = ml_service.is_healthy()
            return HealthResponse(**health_data)

    except Exception as e:
        request_id = getattr(request.state, "request_id", None)
        logger.error(f"Health check failed: {str(e)}", request_id=request_id)
        raise HTTPException(status_code=503, detail="Service unhealthy")
