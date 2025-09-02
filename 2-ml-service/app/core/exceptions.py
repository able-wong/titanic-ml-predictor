"""
Custom exception classes for the FastAPI ML Service.

This module provides custom exception classes with detailed error handling,
structured error responses, and proper HTTP status codes for different error scenarios.
"""

from typing import Dict, Any, Optional, List
from fastapi import HTTPException, status
from pydantic import BaseModel
import traceback
import time


class ErrorDetail(BaseModel):
    """Standardized error detail structure."""

    error_code: str
    message: str
    details: Dict[str, Any] = {}
    timestamp: float = None
    request_id: Optional[str] = None

    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = time.time()
        super().__init__(**data)


class MLServiceError(Exception):
    """Base exception class for ML service errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "ML_SERVICE_ERROR",
        details: Dict[str, Any] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = time.time()
        super().__init__(self.message)

    def to_error_detail(self, request_id: str = None) -> ErrorDetail:
        """Convert exception to structured error detail."""
        return ErrorDetail(
            error_code=self.error_code,
            message=self.message,
            details=self.details,
            timestamp=self.timestamp,
            request_id=request_id,
        )

    def to_http_exception(self, request_id: str = None) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code, detail=self.to_error_detail(request_id).dict()
        )


class ValidationError(MLServiceError):
    """Exception for input validation errors."""

    def __init__(
        self, message: str, field_errors: Dict[str, List[str]] = None, **kwargs
    ):
        details = kwargs.pop("details", {})
        if field_errors:
            details["field_errors"] = field_errors

        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
            **kwargs,
        )


class ModelNotLoadedError(MLServiceError):
    """Exception for when ML models are not loaded."""

    def __init__(self, model_name: str = None, **kwargs):
        message = (
            f"ML model '{model_name}' is not loaded"
            if model_name
            else "ML models are not loaded"
        )
        details = kwargs.get("details", {})
        if model_name:
            details["model_name"] = model_name

        super().__init__(
            message=message,
            error_code="MODEL_NOT_LOADED",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            **kwargs,
        )


class PredictionError(MLServiceError):
    """Exception for prediction computation errors."""

    def __init__(
        self, message: str, model_name: str = None, status_code: int = None, **kwargs
    ):
        details = kwargs.pop("details", {})
        if model_name:
            details["model_name"] = model_name

        # Default to 500, but allow override for specific cases
        default_status = status_code or status.HTTP_500_INTERNAL_SERVER_ERROR

        super().__init__(
            message=message,
            error_code="PREDICTION_ERROR",
            details=details,
            status_code=default_status,
            **kwargs,
        )


class PredictionInputError(PredictionError):
    """Exception for prediction input validation errors."""

    def __init__(
        self, message: str, field_errors: Dict[str, List[str]] = None, **kwargs
    ):
        details = kwargs.get("details", {})
        if field_errors:
            details["field_errors"] = field_errors

        kwargs["details"] = details
        super().__init__(
            message=message, status_code=status.HTTP_400_BAD_REQUEST, **kwargs
        )
        self.error_code = "PREDICTION_INPUT_ERROR"


class ModelUnavailableError(PredictionError):
    """Exception for when models are temporarily unavailable."""

    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(
            message=message,
            model_name=model_name,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            **kwargs,
        )
        self.error_code = "MODEL_UNAVAILABLE"


class AuthenticationError(MLServiceError):
    """Exception for authentication errors."""

    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=status.HTTP_401_UNAUTHORIZED,
            **kwargs,
        )


class AuthorizationError(MLServiceError):
    """Exception for authorization errors."""

    def __init__(
        self, message: str = "Access denied", required_permission: str = None, **kwargs
    ):
        details = kwargs.get("details", {})
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
            **kwargs,
        )


class ConfigurationError(MLServiceError):
    """Exception for configuration errors."""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        details = kwargs.get("details", {})
        if config_key:
            details["config_key"] = config_key

        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            **kwargs,
        )


class ExternalServiceError(MLServiceError):
    """Exception for external service integration errors."""

    def __init__(
        self,
        message: str,
        service_name: str = None,
        service_status: int = None,
        **kwargs,
    ):
        details = kwargs.get("details", {})
        if service_name:
            details["service_name"] = service_name
        if service_status:
            details["service_status"] = service_status

        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY,
            **kwargs,
        )


class BusinessLogicError(MLServiceError):
    """Exception for business logic violations."""

    def __init__(self, message: str, rule_violated: str = None, **kwargs):
        details = kwargs.get("details", {})
        if rule_violated:
            details["rule_violated"] = rule_violated

        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            **kwargs,
        )


def create_error_response(
    error_code: str,
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Dict[str, Any] = None,
    request_id: str = None,
    include_traceback: bool = False,
) -> HTTPException:
    """
    Create a standardized error response.

    Args:
        error_code: Error code identifier
        message: Human-readable error message
        status_code: HTTP status code
        details: Additional error details
        request_id: Request ID for tracing
        include_traceback: Whether to include traceback in details

    Returns:
        HTTPException: Formatted HTTP exception
    """
    error_details = details or {}

    if include_traceback:
        error_details["traceback"] = traceback.format_exc()

    error_detail = ErrorDetail(
        error_code=error_code,
        message=message,
        details=error_details,
        request_id=request_id,
    )

    return HTTPException(status_code=status_code, detail=error_detail.dict())


def handle_pydantic_validation_error(
    exc: Exception, request_id: str = None
) -> HTTPException:
    """
    Convert Pydantic validation errors to standardized format.

    Args:
        exc: Pydantic ValidationError
        request_id: Request ID for tracing

    Returns:
        HTTPException: Formatted validation error
    """
    field_errors = {}

    # Handle Pydantic validation errors
    if hasattr(exc, "errors"):
        for error in exc.errors():
            field_name = ".".join(str(x) for x in error.get("loc", []))
            error_msg = error.get("msg", "Invalid value")

            if field_name not in field_errors:
                field_errors[field_name] = []
            field_errors[field_name].append(error_msg)

    validation_error = ValidationError(
        message="Invalid input data provided", field_errors=field_errors
    )

    return validation_error.to_http_exception(request_id)
