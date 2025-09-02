"""
Pytest configuration and shared fixtures for the test suite.

This module provides common test fixtures, configuration, and utilities
used across all test modules.
"""

import pytest
import pytest_asyncio
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
import tempfile

# Add project root to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
import pickle

# Import application modules
from app.services.health_checker import EnhancedHealthChecker


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_config():
    """Mock application configuration for testing."""
    config_data = {
        "environment": "test",
        "api": {
            "host": "127.0.0.1",
            "port": 8000,
            "cors_origins": ["http://localhost:3000"],
        },
        "jwt": {
            "algorithm": "RS256",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...test_key...\n-----END RSA PRIVATE KEY-----",
            "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...test_key...\n-----END PUBLIC KEY-----",
            "access_token_expire_minutes": 30,
        },
        "logging": {"level": "DEBUG", "format": "json"},
        "rate_limiting": {
            "redis_url": "redis://localhost:6379/0",
            "default_rate": "100/minute",
            "prediction_rate": "50/minute",
            "health_rate": "200/minute",
        },
    }

    class MockConfig:
        def __init__(self):
            for key, value in config_data.items():
                if key == "environment":
                    # Skip environment as it's a property
                    continue
                elif isinstance(value, dict):
                    # Create nested mock objects for dictionaries
                    setattr(self, key, type("MockSubConfig", (), value))
                else:
                    setattr(self, key, value)

        @property
        def environment(self):
            return "test"

    return MockConfig()


@pytest.fixture
def mock_models_dir():
    """Create a temporary directory with mock model files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create mock model files
        mock_lr_model = LogisticRegression()
        mock_dt_model = DecisionTreeClassifier()

        # Create fake training data to fit models
        X = np.random.random((100, 10))
        y = np.random.randint(0, 2, 100)

        mock_lr_model.fit(X, y)
        mock_dt_model.fit(X, y)

        # Save models
        with open(os.path.join(temp_dir, "logistic_model.pkl"), "wb") as f:
            pickle.dump(mock_lr_model, f)

        with open(os.path.join(temp_dir, "decision_tree_model.pkl"), "wb") as f:
            pickle.dump(mock_dt_model, f)

        # Create label encoders
        mock_encoders = {
            "sex": {"classes_": np.array(["female", "male"])},
            "embarked": {"classes_": np.array(["C", "Q", "S"])},
        }

        with open(os.path.join(temp_dir, "label_encoders.pkl"), "wb") as f:
            pickle.dump(mock_encoders, f)

        # Create evaluation results
        evaluation_results = {
            "logistic_regression_accuracy": 0.832,
            "decision_tree_accuracy": 0.802,
            "ensemble_accuracy": 0.817,
        }

        import json

        with open(os.path.join(temp_dir, "evaluation_results.json"), "w") as f:
            json.dump(evaluation_results, f)

        yield temp_dir


@pytest_asyncio.fixture
async def mock_ml_service(mock_models_dir):
    """Create a mock ML service for testing."""
    with patch("app.services.ml_service.ml_service") as mock_service:
        mock_service.is_loaded = True
        mock_service.models_dir = mock_models_dir
        mock_service.logistic_model = Mock()
        mock_service.decision_tree_model = Mock()
        mock_service.label_encoders = {
            "sex": Mock(transform=Mock(return_value=[0])),
            "embarked": Mock(transform=Mock(return_value=[0])),
        }
        mock_service.model_accuracy = {
            "logistic_regression": 0.832,
            "decision_tree": 0.802,
            "ensemble": 0.817,
        }

        # Mock prediction methods
        mock_service.predict_survival = AsyncMock(
            return_value={
                "individual_models": {
                    "logistic_regression": {
                        "probability": 0.888,
                        "prediction": "survived",
                    },
                    "decision_tree": {"probability": 1.000, "prediction": "survived"},
                },
                "ensemble_result": {
                    "probability": 0.944,
                    "prediction": "survived",
                    "confidence": 0.888,
                    "confidence_level": "high",
                },
            }
        )

        mock_service.is_healthy = Mock(
            return_value={
                "status": "healthy",
                "models_loaded": True,
                "preprocessor_ready": True,
                "model_accuracy": mock_service.model_accuracy,
            }
        )

        mock_service.get_feature_columns = Mock(
            return_value=[
                "pclass",
                "sex",
                "age",
                "sibsp",
                "parch",
                "fare",
                "embarked",
                "family_size",
                "is_alone",
                "age_group",
            ]
        )

        mock_service.load_models = AsyncMock()

        yield mock_service


@pytest.fixture
def valid_passenger_data():
    """Valid passenger data for testing."""
    return {
        "pclass": 1,
        "sex": "female",
        "age": 25.0,
        "sibsp": 0,
        "parch": 0,
        "fare": 100.0,
        "embarked": "S",
    }


@pytest.fixture
def invalid_passenger_data():
    """Invalid passenger data for testing validation."""
    return [
        # Out of range values
        {
            "pclass": 4,  # Invalid class
            "sex": "female",
            "age": 25.0,
            "sibsp": 0,
            "parch": 0,
            "fare": 100.0,
            "embarked": "S",
        },
        # Invalid string values
        {
            "pclass": 1,
            "sex": "other",  # Invalid sex
            "age": 25.0,
            "sibsp": 0,
            "parch": 0,
            "fare": 100.0,
            "embarked": "S",
        },
        # Negative values
        {
            "pclass": 1,
            "sex": "male",
            "age": -5.0,  # Invalid age
            "sibsp": 0,
            "parch": 0,
            "fare": 100.0,
            "embarked": "S",
        },
        # SQL injection attempt
        {
            "pclass": 1,
            "sex": "male'; DROP TABLE users; --",
            "age": 25.0,
            "sibsp": 0,
            "parch": 0,
            "fare": 100.0,
            "embarked": "S",
        },
    ]


@pytest.fixture
def mock_jwt_token():
    """Mock JWT token for authentication tests."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test_token_payload.test_signature"


@pytest.fixture
def mock_auth_headers(mock_jwt_token):
    """Mock authentication headers."""
    return {"Authorization": f"Bearer {mock_jwt_token}"}


@pytest.fixture
def app_client(mock_config, mock_ml_service):
    """Create FastAPI test client with mocked dependencies."""
    # Mock the configuration and ML service
    with (
        patch("main.app_config", mock_config),
        patch("main.ml_service", mock_ml_service),
        patch("app.core.config.config_manager") as mock_config_manager,
    ):
        mock_config_manager.load_config.return_value = mock_config
        mock_config_manager.config = mock_config

        # Import the app after mocking
        from main import app

        from fastapi.testclient import TestClient

        client = TestClient(app)
        yield client


@pytest.fixture
def health_checker_mock():
    """Mock health checker for testing."""
    mock_checker = Mock(spec=EnhancedHealthChecker)

    # Mock successful health check results
    mock_checker.run_all_checks = AsyncMock(
        return_value={
            "status": "healthy",
            "timestamp": "2025-09-02T15:00:00.000Z",
            "duration_ms": 42.5,
            "summary": {
                "total_checks": 5,
                "healthy_count": 5,
                "degraded_count": 0,
                "unhealthy_count": 0,
            },
            "checks": {
                "ml_models": {"status": "healthy", "message": "All models loaded"},
                "preprocessor": {"status": "healthy", "message": "Preprocessor ready"},
                "configuration": {"status": "healthy", "message": "Config valid"},
                "system_resources": {"status": "healthy", "message": "Resources OK"},
                "model_files": {"status": "healthy", "message": "Files accessible"},
            },
        }
    )

    mock_checker.run_startup_checks = AsyncMock(
        return_value={
            "status": "startup_success",
            "message": "All critical dependencies validated",
            "timestamp": "2025-09-02T15:00:00.000Z",
            "duration_ms": 1.2,
            "checks": {
                "ml_models": {"status": "healthy"},
                "preprocessor": {"status": "healthy"},
                "configuration": {"status": "healthy"},
                "model_files": {"status": "healthy"},
            },
        }
    )

    return mock_checker


@pytest.fixture(autouse=True)
def mock_rate_limiter():
    """Mock rate limiter for testing."""
    with patch("app.api.middleware.rate_limiter.limiter") as mock_limiter:
        mock_limiter.limit = lambda rate: lambda func: func
        yield mock_limiter


@pytest.fixture
def sample_test_data():
    """Sample data for integration tests."""
    return {
        "valid_requests": [
            {
                "pclass": 1,
                "sex": "female",
                "age": 29.0,
                "sibsp": 0,
                "parch": 0,
                "fare": 211.3375,
                "embarked": "S",
            },
            {
                "pclass": 3,
                "sex": "male",
                "age": 22.0,
                "sibsp": 1,
                "parch": 0,
                "fare": 7.25,
                "embarked": "S",
            },
        ],
        "expected_responses": [
            {"prediction": "survived", "confidence_level": "high"},
            {"prediction": "did_not_survive", "confidence_level": "medium"},
        ],
    }


# Pytest markers for different test categories
pytestmark = [
    pytest.mark.asyncio,
]
