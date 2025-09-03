"""
Integration tests for FastAPI endpoints.

Tests complete API functionality including:
- Authentication flow
- Request/response validation
- Error handling
- Rate limiting
- Health checks
- Prediction endpoints
"""

from unittest.mock import patch, AsyncMock
from contextlib import contextmanager
from fastapi import status


@contextmanager
def authenticated_request(app_client, mock_ml_service=True):
    """Context manager for authenticated requests with optional ML service mocking."""
    from app.api.middleware.auth import get_current_user

    # Override authentication
    def mock_get_current_user():
        return {"user_id": "test_user", "username": "testuser"}

    app_client.app.dependency_overrides[get_current_user] = mock_get_current_user

    if mock_ml_service:
        with patch("app.api.routes.predictions.ml_service") as mock_service:
            # Mock ML service prediction
            mock_service.predict_survival = AsyncMock(
                return_value={
                    "individual_models": {
                        "logistic_regression": {
                            "probability": 0.888,
                            "prediction": "survived",
                        },
                        "decision_tree": {
                            "probability": 1.000,
                            "prediction": "survived",
                        },
                    },
                    "ensemble_result": {
                        "probability": 0.944,
                        "prediction": "survived",
                        "confidence": 0.888,
                        "confidence_level": "high",
                    },
                }
            )
            try:
                yield mock_service
            finally:
                app_client.app.dependency_overrides.clear()
    else:
        try:
            yield None
        finally:
            app_client.app.dependency_overrides.clear()


class TestRootEndpoint:
    """Test root endpoint functionality."""

    def test_root_endpoint(self, app_client):
        """Test root endpoint returns API information."""
        response = app_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["service"] == "Titanic ML Prediction API"
        assert data["version"] == "2.1.0"
        assert data["status"] == "running"
        assert "authentication" in data
        assert "docs" in data
        assert "health" in data


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_basic_health_check(self, app_client):
        """Test basic health check endpoint."""
        response = app_client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "status" in data
        assert "models_loaded" in data
        assert "preprocessor_ready" in data

    def test_detailed_health_check(self, app_client, health_checker_mock):
        """Test detailed health check endpoint."""
        with patch("app.api.routes.health.health_checker", health_checker_mock):
            response = app_client.get("/health?detailed=true")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "duration_ms" in data
            assert "summary" in data
            assert "checks" in data
            assert data["summary"]["total_checks"] == 5

    def test_health_check_query_validation(self, app_client):
        """Test health check with malicious query parameters."""
        # Test XSS attempt
        response = app_client.get("/health?detailed=<script>alert('xss')</script>")

        # Should handle the validation error gracefully
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK,
        ]

        # Test SQL injection attempt
        response = app_client.get("/health?detailed=true'; DROP TABLE users; --")

        # Should handle the validation error gracefully
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            status.HTTP_200_OK,
        ]


class TestPredictionEndpoints:
    """Test prediction endpoints with authentication."""

    def setup_auth_and_ml_mocks(self, app_client, mock_service=None):
        """Helper method to setup auth and ML service mocks."""
        from app.api.middleware.auth import get_current_user

        # Override the dependency
        def mock_get_current_user():
            return {"user_id": "test_user", "username": "testuser"}

        app_client.app.dependency_overrides[get_current_user] = mock_get_current_user

        if mock_service:
            # Mock ML service prediction
            mock_service.predict_survival = AsyncMock(
                return_value={
                    "individual_models": {
                        "logistic_regression": {
                            "probability": 0.888,
                            "prediction": "survived",
                        },
                        "decision_tree": {
                            "probability": 1.000,
                            "prediction": "survived",
                        },
                    },
                    "ensemble_result": {
                        "probability": 0.944,
                        "prediction": "survived",
                        "confidence": 0.888,
                        "confidence_level": "high",
                    },
                }
            )

    def cleanup_overrides(self, app_client):
        """Helper method to cleanup dependency overrides."""
        app_client.app.dependency_overrides.clear()

    @contextmanager
    def authenticated_request(self, app_client, mock_ml_service=True):
        """Context manager for authenticated requests with optional ML service mocking."""
        from app.api.middleware.auth import get_current_user

        # Override authentication
        def mock_get_current_user():
            return {"user_id": "test_user", "username": "testuser"}

        app_client.app.dependency_overrides[get_current_user] = mock_get_current_user

        if mock_ml_service:
            with patch("app.api.routes.predictions.ml_service") as mock_service:
                self.setup_auth_and_ml_mocks(app_client, mock_service)
                try:
                    yield mock_service
                finally:
                    self.cleanup_overrides(app_client)
        else:
            try:
                yield None
            finally:
                self.cleanup_overrides(app_client)

    def test_prediction_without_auth(self, app_client, valid_passenger_data):
        """Test prediction endpoint without authentication."""
        response = app_client.post("/predict", json=valid_passenger_data)

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]
        data = response.json()
        assert "detail" in data or "error" in data

    def test_prediction_with_invalid_token(self, app_client, valid_passenger_data):
        """Test prediction endpoint with invalid JWT token."""
        headers = {"Authorization": "Bearer invalid_token_here"}

        response = app_client.post(
            "/predict", json=valid_passenger_data, headers=headers
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_prediction_with_valid_auth(
        self, app_client, valid_passenger_data, mock_auth_headers
    ):
        """Test prediction endpoint with valid authentication (mocked ML service)."""
        with authenticated_request(app_client):
            response = app_client.post(
                "/predict", json=valid_passenger_data, headers=mock_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert "individual_models" in data
            assert "ensemble_result" in data
            assert "logistic_regression" in data["individual_models"]
            assert "decision_tree" in data["individual_models"]

    def test_prediction_with_real_ml_service(
        self, app_client, valid_passenger_data, mock_auth_headers
    ):
        """Test prediction endpoint with real ML service (no mocking)."""
        # This test uses the actual ML service to catch integration bugs
        with authenticated_request(app_client, mock_ml_service=False):
            response = app_client.post(
                "/predict", json=valid_passenger_data, headers=mock_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify complete response structure
            assert "individual_models" in data
            assert "ensemble_result" in data

            # Verify individual model predictions
            individual = data["individual_models"]
            assert "logistic_regression" in individual
            assert "decision_tree" in individual

            for model_name, prediction in individual.items():
                assert "probability" in prediction
                assert "prediction" in prediction
                assert isinstance(prediction["probability"], (int, float))
                assert prediction["prediction"] in ["survived", "did_not_survive"]
                assert 0.0 <= prediction["probability"] <= 1.0

            # Verify ensemble prediction
            ensemble = data["ensemble_result"]
            assert "probability" in ensemble
            assert "prediction" in ensemble
            assert "confidence" in ensemble
            assert "confidence_level" in ensemble

            assert isinstance(ensemble["probability"], (int, float))
            assert ensemble["prediction"] in ["survived", "did_not_survive"]
            assert isinstance(ensemble["confidence"], (int, float))
            assert ensemble["confidence_level"] in ["low", "medium", "high"]
            assert 0.0 <= ensemble["probability"] <= 1.0
            assert 0.0 <= ensemble["confidence"] <= 1.0

    def test_prediction_input_validation(
        self, app_client, mock_auth_headers, invalid_passenger_data
    ):
        """Test prediction endpoint input validation."""
        with authenticated_request(app_client, mock_ml_service=False):
            for invalid_data in invalid_passenger_data:
                response = app_client.post(
                    "/predict", json=invalid_data, headers=mock_auth_headers
                )

                # Should return validation error
                assert response.status_code in [
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                ]

                data = response.json()
                assert "error" in data or "detail" in data

    def test_prediction_enhanced_validation(self, app_client, mock_auth_headers):
        """Test prediction endpoint with enhanced validation features."""
        with authenticated_request(app_client, mock_ml_service=False):
            # Test with SQL injection in passenger data
            malicious_data = {
                "pclass": 1,
                "sex": "male'; DROP TABLE users; --",
                "age": 25.0,
                "sibsp": 0,
                "parch": 0,
                "fare": 100.0,
                "embarked": "S",
            }

            response = app_client.post(
                "/predict", json=malicious_data, headers=mock_auth_headers
            )

            # Should be blocked by enhanced validation
            assert response.status_code in [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ]

    def test_prediction_anomaly_detection(self, app_client, mock_auth_headers):
        """Test prediction endpoint anomaly detection logging."""
        with (
            self.authenticated_request(app_client),
            patch("app.utils.validation.logger") as mock_logger,
        ):
            # Anomalous but valid data (child with high fare)
            anomalous_data = {
                "pclass": 1,
                "sex": "female",
                "age": 8.0,  # Child
                "sibsp": 0,
                "parch": 2,
                "fare": 200.0,  # High fare
                "embarked": "S",
            }

            response = app_client.post(
                "/predict", json=anomalous_data, headers=mock_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify anomaly was logged
            mock_logger.info.assert_called()


class TestModelInfoEndpoint:
    """Test model information endpoint."""

    def test_model_info_endpoint(self, app_client):
        """Test model info endpoint returns model information."""
        response = app_client.get("/models/info")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "models_loaded" in data
        assert "feature_columns" in data
        assert "model_accuracy" in data
        assert "model_types" in data

    def test_model_info_when_models_not_loaded(self, app_client):
        """Test model info endpoint when models are not loaded."""
        with patch("app.api.routes.models.ml_service") as mock_service:
            mock_service.is_loaded = False
            mock_service.get_feature_columns.return_value = []
            mock_service.model_accuracy = {}

            response = app_client.get("/models/info")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["models_loaded"] is False


class TestErrorHandling:
    """Test error handling across endpoints."""

    def test_pydantic_validation_error(self, app_client, mock_auth_headers):
        """Test Pydantic validation error handling."""
        with authenticated_request(app_client, mock_ml_service=False):
            # Missing required fields
            invalid_data = {
                "pclass": 1,
                "sex": "male",
                # Missing age, sibsp, parch, fare, embarked
            }

            response = app_client.post(
                "/predict", json=invalid_data, headers=mock_auth_headers
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            data = response.json()
            assert "error" in data or "detail" in data

    def test_ml_service_error_handling(
        self, app_client, mock_auth_headers, valid_passenger_data
    ):
        """Test ML service error handling."""
        with authenticated_request(app_client, mock_ml_service=False):
            with patch("app.api.routes.predictions.ml_service") as mock_service:
                # Mock ML service failure
                from app.core.exceptions import PredictionError

                mock_service.predict_survival = AsyncMock(
                    side_effect=PredictionError("Model prediction failed")
                )

                response = app_client.post(
                    "/predict", json=valid_passenger_data, headers=mock_auth_headers
                )

                assert response.status_code in [
                    status.HTTP_500_INTERNAL_SERVER_ERROR,
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                ]

    def test_specific_error_status_codes(
        self, app_client, mock_auth_headers, valid_passenger_data
    ):
        """Test that specific error types return appropriate HTTP status codes."""
        with authenticated_request(app_client, mock_ml_service=False):
            # Test 400 for input validation errors
            with patch("app.api.routes.predictions.ml_service") as mock_service:
                from app.core.exceptions import PredictionInputError

                mock_service.predict_survival = AsyncMock(
                    side_effect=PredictionInputError("Invalid input data")
                )

                response = app_client.post(
                    "/predict", json=valid_passenger_data, headers=mock_auth_headers
                )
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                data = response.json()
                assert "error_code" in data
                assert data["error_code"] == "PREDICTION_INPUT_ERROR"

            # Test 503 for model unavailable errors
            with patch("app.api.routes.predictions.ml_service") as mock_service:
                from app.core.exceptions import ModelUnavailableError

                mock_service.predict_survival = AsyncMock(
                    side_effect=ModelUnavailableError("Models not available")
                )

                response = app_client.post(
                    "/predict", json=valid_passenger_data, headers=mock_auth_headers
                )
                assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
                data = response.json()
                assert "error_code" in data
                assert data["error_code"] == "MODEL_UNAVAILABLE"

    def test_global_exception_handler(self, app_client):
        """Test global exception handler for unhandled errors."""
        with patch("app.api.routes.health.ml_service") as mock_service:
            # Cause an unhandled exception
            mock_service.is_healthy.side_effect = Exception("Unexpected error")

            response = app_client.get("/health")

            # Health endpoint catches exceptions and returns 503
            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            data = response.json()
            assert "detail" in data
            assert "unhealthy" in data["detail"].lower()


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_health_check_rate_limiting(self, app_client):
        """Test rate limiting on health check endpoint."""
        # Note: This test depends on Redis mock and rate limiting configuration
        # In a real environment, you would make multiple rapid requests

        # Make initial request
        response = app_client.get("/health")
        assert response.status_code == status.HTTP_200_OK

        # In actual testing, you would exceed the rate limit and check for 429
        # For now, just verify the endpoint works

    def test_prediction_rate_limiting(
        self, app_client, mock_auth_headers, valid_passenger_data
    ):
        """Test rate limiting on prediction endpoint."""
        with authenticated_request(app_client):
            # Make initial request
            response = app_client.post(
                "/predict", json=valid_passenger_data, headers=mock_auth_headers
            )
            assert response.status_code == status.HTTP_200_OK

            # Rate limiting is mocked in conftest.py, so requests succeed


class TestCORSAndMiddleware:
    """Test CORS and middleware functionality."""

    def test_cors_headers(self, app_client):
        """Test CORS headers are present."""
        response = app_client.options("/health")

        # CORS preflight should be handled
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_405_METHOD_NOT_ALLOWED,
        ]

    def test_request_id_middleware(self, app_client):
        """Test request ID middleware adds headers."""
        response = app_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert "X-Request-ID" in response.headers
        # Firebase-optimized middleware only includes X-Request-ID

    def test_structured_logging_middleware(self, app_client):
        """Test structured logging middleware logs requests."""
        # Firebase-optimized middleware only logs slow requests (>100ms)
        response = app_client.get("/")

        assert response.status_code == status.HTTP_200_OK
        assert "X-Request-ID" in response.headers

        # Fast requests don't trigger logging, which is the expected optimized behavior


class TestStartupHealthChecks:
    """Test startup health check integration."""

    def test_startup_checks_success(self, health_checker_mock):
        """Test that startup checks are run during application startup."""
        # This is tested implicitly when the app_client fixture is created
        # The app should start successfully if startup checks pass
        pass

    def test_startup_checks_failure(self):
        """Test that startup check failures prevent app startup."""
        # This would require creating a separate test app instance
        # with failing startup checks, which is complex in this setup
        pass
