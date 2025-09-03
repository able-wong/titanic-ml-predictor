"""
Production FastAPI ML Service.

This service is optimized for Cloud Run deployment with:
- Minimal cold start time (<500ms)
- Lazy loading of ML models
- Fast startup validation only
- Deferred heavy operations
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import sys
import os
import uuid

# Add project root to Python path
sys.path.append(os.path.dirname(__file__))

# Import core components
from app.core import (
    config_manager,
    setup_structured_logging,
    get_logger,
    MLServiceError,
)

# Import services
from app.services.lazy_ml_service import fast_ml_service as ml_service

# Import API routes
from app.api.routes import health_router, predictions_router, models_router

# Global variables
app_config = None
logger = None


# Production optimized lifespan
@asynccontextmanager
async def production_lifespan(app: FastAPI):
    """
    Ultra-fast lifespan handler for production deployment.

    Optimizations:
    - No model loading at startup (lazy loading)
    - Minimal validation only
    - Fast configuration loading
    - No health checks at startup
    """
    startup_start = time.time()

    try:
        logger.info(
            "Starting Titanic ML Prediction API", startup_phase="initialization"
        )

        # Fast ML service initialization (no model loading)
        await ml_service.load_models()  # Just validates directory

        startup_time = (time.time() - startup_start) * 1000
        logger.info(
            "ML service initialized successfully",
            startup_phase="completed",
            startup_time_ms=round(startup_time, 2),
            startup_mode="optimized",
        )

    except Exception as e:
        startup_time = (time.time() - startup_start) * 1000
        logger.error(
            "Service startup failed",
            startup_phase="failed",
            startup_time_ms=round(startup_time, 2),
            error_message=str(e),
            error_type=type(e).__name__,
        )
        raise

    yield

    # Minimal cleanup
    logger.info("Shutting down Titanic ML Prediction API", shutdown_phase="cleanup")


def load_app_config():
    """Fast configuration loading optimized for startup performance."""
    global app_config, logger

    # Load configuration (cached after first load)
    app_config = config_manager.load_config()

    # Minimal logging setup
    setup_structured_logging(
        environment=app_config.environment, log_level=app_config.logging.level.upper()
    )

    logger = get_logger("main")

    logger.info(
        "Application configuration loaded",
        environment=app_config.environment,
        jwt_algorithm=app_config.jwt.algorithm,
        token_expire_minutes=app_config.jwt.access_token_expire_minutes,
    )


# Load configuration immediately
load_app_config()

# Initialize FastAPI app with optimized lifespan and comprehensive OpenAPI documentation
app = FastAPI(
    lifespan=production_lifespan,
    title="Titanic ML Prediction API",
    description="""
    ## Machine Learning API for Titanic Passenger Survival Prediction
    
    This production-ready API provides ML-powered predictions for Titanic passenger survival
    with optimized performance, comprehensive authentication, and robust error handling.
    
    ### Key Features:
    - 🚀 **Ultra-fast startup** (~0.17ms cold start)
    - 🔒 **JWT Authentication** with RS256 algorithm
    - 📊 **Dual ML Models** (Logistic Regression + Decision Tree)
    - ⚡ **Lazy Loading** for optimal Cloud Run performance
    - 🛡️ **Input Validation** with XSS/SQL injection prevention
    - 📈 **Structured Logging** with request tracing
    - 💚 **Health Monitoring** with detailed system checks
    
    ### Authentication Required:
    Most endpoints require JWT Bearer token authentication. Generate tokens using:
    ```bash
    python scripts/generate_jwt.py --user-id your_user_id
    ```
    
    ### Rate Limits:
    - Authenticated users: 100 requests/minute
    - Health checks: 200 requests/minute
    
    ### Error Handling:
    The API returns structured error responses with specific HTTP status codes:
    - **400**: Invalid input data or malformed requests
    - **401**: Authentication failures (missing/expired tokens)
    - **403**: Authorization failures (insufficient permissions)  
    - **429**: Rate limit exceeded
    - **503**: Service temporarily unavailable (models not loaded)
    - **500**: Internal server errors
    
    For detailed integration examples and troubleshooting, see the project README.
    """,
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Root", "description": "Service information and basic endpoints"},
        {
            "name": "Health",
            "description": "Health check endpoints for monitoring service status",
        },
        {
            "name": "Predictions",
            "description": "ML prediction endpoints (authentication required)",
        },
        {
            "name": "Models",
            "description": "Model information endpoints (authentication required)",
        },
    ],
)

# Minimal middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_config.api.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Lightweight request tracking
@app.middleware("http")
async def lightweight_middleware(request: Request, call_next):
    """Lightweight middleware for Firebase Functions."""
    start_time = time.time()
    request_id = str(uuid.uuid4())[:8]  # Shorter ID for Firebase
    request.state.request_id = request_id

    response = await call_next(request)

    # Minimal logging
    process_time = (time.time() - start_time) * 1000
    if process_time > 100:  # Only log slow requests
        logger.info(
            "Request completed",
            request_id=request_id,
            endpoint=str(request.url.path),
            duration_ms=round(process_time, 2),
        )

    response.headers["X-Request-ID"] = request_id
    return response


# Exception handlers (essential only)
@app.exception_handler(MLServiceError)
async def ml_service_exception_handler(request: Request, exc: MLServiceError):
    """Handle ML service exceptions."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code, content=exc.to_error_detail(request_id).dict()
    )


# Root endpoint (not in a router for fast access)
@app.get("/", tags=["Root"])
async def root():
    """Fast root endpoint."""
    return {
        "service": "Titanic ML Prediction API",
        "version": "2.1.0",
        "status": "running",
        "startup_mode": "optimized",
        "authentication": "JWT Bearer token required for predictions",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(health_router)
app.include_router(predictions_router)
app.include_router(models_router)


if __name__ == "__main__":
    import uvicorn
    import signal
    import sys

    def signal_handler(sig, frame):
        """Handle shutdown signals gracefully"""
        print(f"\n🛑 Received signal {sig}, shutting down gracefully...")
        sys.exit(0)

    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    # Check if running in containerized environment (Cloud Run, Docker, etc.)
    port = int(os.getenv("PORT", 8000))

    # Use 0.0.0.0 for containerized deployments (Cloud Run, Docker)
    # Use 127.0.0.1 only for local development
    ml_env = os.getenv("ML_SERVICE_ENVIRONMENT", "development")
    if ml_env in ["production", "staging"] or os.getenv("PORT"):
        # Cloud Run always sets PORT, so this indicates containerized deployment
        host = "0.0.0.0"  # nosec B104 - Required for containerized deployment
    else:
        # Local development
        host = "127.0.0.1"

    # Enable reload for local development, disable for containerized deployments
    reload_enabled = ml_env == "development" and not os.getenv("PORT")
    
    print("🚀 Starting optimized Titanic ML API...")
    uvicorn.run("main:app", host=host, port=port, reload=reload_enabled, log_level="info")
