"""
Core components for the Titanic ML Service.

Includes:
- config: Configuration management
- exceptions: Custom exception classes
- logging_config: Structured logging setup
"""

from .config import config_manager
from .exceptions import (
    MLServiceError,
    ValidationError,
    ModelNotLoadedError,
    PredictionError,
    ConfigurationError,
    handle_pydantic_validation_error,
    create_error_response,
)
from .logging_config import setup_structured_logging, get_logger, StructuredLogger

__all__ = [
    "config_manager",
    "MLServiceError",
    "ValidationError",
    "ModelNotLoadedError",
    "PredictionError",
    "ConfigurationError",
    "handle_pydantic_validation_error",
    "create_error_response",
    "setup_structured_logging",
    "get_logger",
    "StructuredLogger",
]
