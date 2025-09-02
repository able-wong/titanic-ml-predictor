"""
Structured JSON logging configuration using structlog.

This module provides platform-agnostic structured JSON logging that works
with any cloud platform including Google Cloud, AWS, Azure, and local development.
The JSON output is automatically captured and parsed by modern cloud platforms.
"""

import structlog
import logging
import sys
from typing import Any, Dict
from datetime import datetime, timezone


def add_timestamp(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add ISO 8601 timestamp to log entries."""
    event_dict["timestamp"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    return event_dict


def add_service_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add service-level context to all log entries."""
    event_dict["service"] = "titanic-ml-api"
    event_dict["version"] = "2.0.0"
    return event_dict


def add_log_level(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize log level names for consistency."""
    # Map structlog method names to standard log levels
    level_mapping = {
        'debug': 'DEBUG',
        'info': 'INFO', 
        'warning': 'WARNING',
        'warn': 'WARNING',
        'error': 'ERROR',
        'critical': 'CRITICAL',
        'exception': 'ERROR'
    }
    
    event_dict["level"] = level_mapping.get(method_name.lower(), method_name.upper())
    return event_dict


def filter_sensitive_data(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Remove or mask sensitive information from logs."""
    sensitive_keys = ['password', 'token', 'api_key', 'secret', 'private_key']
    
    def _filter_dict(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                key: "[REDACTED]" if any(sensitive in key.lower() for sensitive in sensitive_keys)
                else _filter_dict(value)
                for key, value in obj.items()
            }
        elif isinstance(obj, list):
            return [_filter_dict(item) for item in obj]
        return obj
    
    return _filter_dict(event_dict)


def setup_structured_logging(environment: str = "development", log_level: str = "INFO") -> None:
    """
    Configure structured JSON logging with platform-agnostic output.
    
    Args:
        environment: Application environment (development/staging/production)
        log_level: Minimum log level to output
        
    This configuration outputs pure JSON to stdout, which is automatically
    captured and parsed by cloud platforms like Google Cloud, AWS, etc.
    """
    
    # Configure standard library logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )
    
    # Configure structlog processors
    processors = [
        # Add service context to all logs
        add_service_context,
        
        # Add standardized timestamp
        add_timestamp,
        
        # Normalize log levels
        add_log_level,
        
        # Filter sensitive information
        filter_sensitive_data,
        
        # Add environment context
        lambda logger, method_name, event_dict: {**event_dict, "environment": environment},
        
        # Convert to JSON for output
        structlog.processors.JSONRenderer(sort_keys=True)
    ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(component: str = None) -> structlog.stdlib.BoundLogger:
    """
    Get a configured structured logger.
    
    Args:
        component: Component name (e.g., 'ml_service', 'auth', 'api')
        
    Returns:
        Configured structured logger with component context
    """
    logger = structlog.get_logger()
    
    if component:
        logger = logger.bind(component=component)
    
    return logger


def add_request_context(
    request_id: str = None,
    user_id: str = None, 
    endpoint: str = None,
    method: str = None
) -> structlog.stdlib.BoundLogger:
    """
    Create a logger with request context bound to it.
    
    Args:
        request_id: Unique request identifier
        user_id: User identifier from authentication
        endpoint: API endpoint being accessed
        method: HTTP method
        
    Returns:
        Logger with request context bound
    """
    logger = structlog.get_logger()
    
    context = {}
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    if endpoint:
        context["endpoint"] = endpoint
    if method:
        context["http_method"] = method
        
    return logger.bind(**context)


class StructuredLogger:
    """
    Convenience class for structured logging with common patterns.
    
    This class provides helper methods for common logging scenarios
    in the ML service application.
    """
    
    def __init__(self, component: str = None):
        """Initialize with optional component context."""
        self.logger = get_logger(component)
    
    def request_started(
        self, 
        request_id: str,
        endpoint: str,
        method: str,
        user_id: str = None,
        **kwargs
    ) -> None:
        """Log the start of a request."""
        self.logger.info(
            "Request started",
            request_id=request_id,
            endpoint=endpoint,
            http_method=method,
            user_id=user_id,
            **kwargs
        )
    
    def request_completed(
        self,
        request_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
        **kwargs
    ) -> None:
        """Log the completion of a request."""
        self.logger.info(
            "Request completed",
            request_id=request_id,
            endpoint=endpoint,
            http_method=method,
            status_code=status_code,
            duration_ms=round(duration_ms, 2),
            user_id=user_id,
            **kwargs
        )
    
    def prediction_completed(
        self,
        request_id: str,
        user_id: str,
        prediction_result: str,
        confidence: float,
        duration_ms: float,
        model_accuracy: Dict[str, float] = None,
        **kwargs
    ) -> None:
        """Log ML prediction completion."""
        log_data = {
            "request_id": request_id,
            "user_id": user_id,
            "prediction_result": prediction_result,
            "confidence": round(confidence, 3),
            "duration_ms": round(duration_ms, 2)
        }
        
        if model_accuracy:
            log_data["model_accuracy"] = model_accuracy
        
        log_data.update(kwargs)
        
        self.logger.info("ML prediction completed", **log_data)
    
    def authentication_event(
        self,
        event_type: str,
        user_id: str = None,
        success: bool = True,
        error_reason: str = None,
        **kwargs
    ) -> None:
        """Log authentication events."""
        log_data = {
            "auth_event_type": event_type,
            "auth_success": success
        }
        
        if user_id:
            log_data["user_id"] = user_id
        if error_reason:
            log_data["auth_error_reason"] = error_reason
            
        log_data.update(kwargs)
        
        level = self.logger.info if success else self.logger.warning
        level(f"Authentication {event_type}", **log_data)
    
    def rate_limit_event(
        self,
        limit_type: str,
        limit_exceeded: bool,
        current_count: int = None,
        limit_threshold: int = None,
        user_id: str = None,
        ip_address: str = None,
        **kwargs
    ) -> None:
        """Log rate limiting events."""
        log_data = {
            "rate_limit_type": limit_type,
            "rate_limit_exceeded": limit_exceeded
        }
        
        if current_count is not None:
            log_data["current_count"] = current_count
        if limit_threshold is not None:
            log_data["limit_threshold"] = limit_threshold
        if user_id:
            log_data["user_id"] = user_id
        if ip_address:
            log_data["client_ip"] = ip_address
            
        log_data.update(kwargs)
        
        level = self.logger.warning if limit_exceeded else self.logger.debug
        level("Rate limit check", **log_data)