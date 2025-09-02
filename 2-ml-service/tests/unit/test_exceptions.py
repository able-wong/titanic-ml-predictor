"""
Unit tests for custom exception classes.

Tests the improved exception handling with more specific HTTP status codes.
"""

from fastapi import status

from app.core.exceptions import (
    PredictionError, PredictionInputError, ModelUnavailableError,
    ModelNotLoadedError, ValidationError, ConfigurationError,
    AuthenticationError, AuthorizationError, ExternalServiceError
)


class TestImprovedExceptions:
    """Test improved exception classes with specific status codes."""
    
    def test_prediction_input_error_returns_400(self):
        """Test PredictionInputError returns 400 Bad Request."""
        exc = PredictionInputError("Invalid input data")
        
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.error_code == "PREDICTION_INPUT_ERROR"
        assert exc.message == "Invalid input data"
    
    def test_model_unavailable_error_returns_503(self):
        """Test ModelUnavailableError returns 503 Service Unavailable."""
        exc = ModelUnavailableError("Models not ready", model_name="logistic_regression")
        
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc.error_code == "MODEL_UNAVAILABLE"
        assert exc.message == "Models not ready"
        assert exc.details["model_name"] == "logistic_regression"
    
    def test_prediction_error_with_custom_status_code(self):
        """Test PredictionError can accept custom status codes."""
        # Default 500
        exc = PredictionError("System error")
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # Custom status code
        exc_custom = PredictionError("Custom error", status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
        assert exc_custom.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    
    def test_model_not_loaded_error_returns_503(self):
        """Test ModelNotLoadedError returns 503 Service Unavailable."""
        exc = ModelNotLoadedError("decision_tree")
        
        assert exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert exc.error_code == "MODEL_NOT_LOADED"
        assert "decision_tree" in exc.message
    
    def test_validation_error_returns_400(self):
        """Test ValidationError returns 400 Bad Request."""
        field_errors = {"age": ["Must be between 0 and 120"], "fare": ["Must be positive"]}
        exc = ValidationError("Validation failed", field_errors=field_errors)
        
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.details["field_errors"] == field_errors
    
    def test_authentication_error_returns_401(self):
        """Test AuthenticationError returns 401 Unauthorized."""
        exc = AuthenticationError("Token expired")
        
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.error_code == "AUTHENTICATION_ERROR"
    
    def test_authorization_error_returns_403(self):
        """Test AuthorizationError returns 403 Forbidden."""
        exc = AuthorizationError("Access denied", required_permission="admin")
        
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.error_code == "AUTHORIZATION_ERROR"
        assert exc.details["required_permission"] == "admin"
    
    def test_configuration_error_returns_500(self):
        """Test ConfigurationError returns 500 Internal Server Error."""
        exc = ConfigurationError("Missing config", config_key="database.url")
        
        assert exc.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert exc.error_code == "CONFIGURATION_ERROR"
        assert exc.details["config_key"] == "database.url"
    
    def test_external_service_error_returns_502(self):
        """Test ExternalServiceError returns 502 Bad Gateway."""
        exc = ExternalServiceError("Service down", service_name="auth_service", service_status=503)
        
        assert exc.status_code == status.HTTP_502_BAD_GATEWAY
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert exc.details["service_name"] == "auth_service"
        assert exc.details["service_status"] == 503
    
    def test_error_detail_conversion(self):
        """Test exception to ErrorDetail conversion."""
        exc = PredictionInputError("Bad data", field_errors={"age": ["Invalid"]})
        error_detail = exc.to_error_detail(request_id="test-123")
        
        assert error_detail.error_code == "PREDICTION_INPUT_ERROR"
        assert error_detail.message == "Bad data"
        assert error_detail.request_id == "test-123"
        assert "field_errors" in error_detail.details
        assert error_detail.timestamp is not None
    
    def test_http_exception_conversion(self):
        """Test exception to HTTPException conversion."""
        exc = ModelUnavailableError("Service temporarily unavailable")
        http_exc = exc.to_http_exception(request_id="req-456")
        
        assert http_exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert http_exc.detail["error_code"] == "MODEL_UNAVAILABLE"
        assert http_exc.detail["message"] == "Service temporarily unavailable"
        assert http_exc.detail["request_id"] == "req-456"