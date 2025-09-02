"""
Rate limiting implementation for the FastAPI ML Service.

This module provides rate limiting functionality using slowapi with Redis backend
for distributed rate limiting across multiple service instances.
"""

import time
from typing import Dict, Optional
from fastapi import Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import config_manager
from app.core.logging_config import get_logger, StructuredLogger


def get_user_id_from_request(request: Request) -> str:
    """
    Extract user ID from JWT token in the request for user-based rate limiting.

    Falls back to IP address if no user ID is available.

    Args:
        request: FastAPI Request object

    Returns:
        str: User ID or IP address for rate limiting key
    """
    try:
        # Try to get user from the request state (set by auth middleware)
        if hasattr(request.state, "current_user") and request.state.current_user:
            user_id = request.state.current_user.get("user_id")
            if user_id:
                return f"user:{user_id}"
    except (AttributeError, KeyError):
        pass

    # Fall back to IP-based rate limiting
    return f"ip:{get_remote_address(request)}"


def get_api_key_from_request(request: Request) -> str:
    """
    Alternative rate limiting strategy based on API key or IP.

    Args:
        request: FastAPI Request object

    Returns:
        str: Rate limiting identifier
    """
    # For now, use IP address - can be extended for API key support
    return get_remote_address(request)


class RateLimiterConfig:
    """Configuration for rate limiting rules."""

    def __init__(self):
        """Initialize rate limiter configuration from app config."""
        self.config = None
        self._initialized = False
        self.logger = get_logger("rate_limiter")
        self.structured_logger = StructuredLogger("rate_limiter")

        # Default rate limiting rules (fallback if config not available)
        self.default_rate_limit = "100/minute"
        self.prediction_limit = "50/minute"  # More restrictive for ML predictions
        self.health_limit = "200/minute"  # More lenient for health checks
        self.auth_limit = "20/minute"  # Conservative for auth operations
        self.storage_backend = "memory"
        self.redis_url = None

    def _ensure_initialized(self):
        """Ensure configuration is loaded."""
        if not self._initialized:
            try:
                if hasattr(config_manager, '_config') and config_manager._config:
                    self.config = config_manager._config
                    rate_config = self.config.rate_limiting
                    
                    # Load rate limits from config
                    self.default_rate_limit = rate_config.limits.default
                    self.prediction_limit = rate_config.limits.predictions
                    self.health_limit = rate_config.limits.health
                    self.auth_limit = rate_config.limits.auth
                    
                    # Load storage configuration
                    self.storage_backend = rate_config.storage_backend
                    if self.storage_backend == "redis":
                        self.redis_url = rate_config.redis.url
                    
                    self._initialized = True
            except (RuntimeError, AttributeError):
                # Configuration not available (e.g., during testing)
                pass

    def get_storage_uri(self) -> str:
        """
        Get storage URI for rate limiting based on configuration.

        Returns:
            str: Storage URI for rate limiting backend
        """
        self._ensure_initialized()
        
        if self.storage_backend == "redis" and self.redis_url:
            return self.redis_url
        else:
            # Default to in-memory storage
            return "memory://"


# Initialize rate limiter configuration
rate_limiter_config = RateLimiterConfig()

# Create limiter instance with configurable storage backend
limiter = Limiter(
    key_func=get_user_id_from_request,
    storage_uri=rate_limiter_config.get_storage_uri(),
    default_limits=[rate_limiter_config.default_rate_limit],
)


# Custom rate limit exceeded handler
async def custom_rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded errors.

    Provides detailed error information and retry headers.

    Args:
        request: FastAPI Request object
        exc: RateLimitExceeded exception

    Returns:
        JSONResponse: Formatted rate limit error
    """
    # Calculate retry after (60 seconds for per-minute limits)
    retry_after = 60
    limit_key = get_user_id_from_request(request)
    request_id = getattr(request.state, "request_id", None)

    # Log the rate limit violation with structured data
    structured_logger = StructuredLogger("rate_limiter")

    # Extract user_id and IP from limit key
    user_id = None
    ip_address = None
    if limit_key.startswith("user:"):
        user_id = limit_key.split(":", 1)[1]
    elif limit_key.startswith("ip:"):
        ip_address = limit_key.split(":", 1)[1]

    structured_logger.rate_limit_event(
        limit_type="request_rate",
        limit_exceeded=True,
        limit_threshold=exc.limit.limit,
        user_id=user_id,
        ip_address=ip_address,
        request_id=request_id,
        endpoint=str(request.url.path),
        http_method=request.method,
        retry_after_seconds=retry_after,
    )

    response_data = {
        "error": "RateLimitExceeded",
        "message": f"Rate limit exceeded: {exc.detail}",
        "details": {"limit": str(exc.limit), "retry_after": retry_after, "limit_key": limit_key},
    }

    # Create JSON response with retry headers
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=response_data,
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": str(exc.limit.limit),
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + retry_after),
        },
    )


def get_rate_limit_headers(request: Request, limit_key: str = None) -> Dict[str, str]:
    """
    Generate rate limit headers for responses.

    Args:
        request: FastAPI Request object
        limit_key: Optional specific limit key

    Returns:
        Dict[str, str]: Headers to include in response
    """
    try:
        if not limit_key:
            limit_key = get_user_id_from_request(request)

        # This would typically query the rate limiter backend
        # For now, return static headers
        return {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Window": "60",
            "X-RateLimit-Policy": "100;w=60",
        }
    except Exception:
        return {}


# Rate limiting decorators for different endpoint types
def prediction_rate_limit():
    """Rate limit decorator for prediction endpoints."""
    return limiter.limit(rate_limiter_config.prediction_limit)


def health_rate_limit():
    """Rate limit decorator for health check endpoints."""
    return limiter.limit(rate_limiter_config.health_limit)


def auth_rate_limit():
    """Rate limit decorator for authentication endpoints."""
    return limiter.limit(rate_limiter_config.auth_limit)


def default_rate_limit():
    """Default rate limit decorator."""
    return limiter.limit(rate_limiter_config.default_rate_limit)
