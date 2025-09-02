# Test Suite Documentation

This directory contains comprehensive unit and integration tests for the Titanic ML Prediction API.

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Shared test fixtures and configuration
├── unit/                    # Unit tests for individual components
│   ├── test_validation.py   # Input validation and sanitization tests
│   ├── test_health.py       # Health check system tests
│   └── ...
├── integration/             # Integration tests for API endpoints
│   ├── test_api_endpoints.py # Full API testing with mocked dependencies
│   └── ...
└── fixtures/                # Test data and fixtures
```

## Running Tests

### Using the Test Runner

```bash
# Run all tests
python run_tests.py all

# Run unit tests only
python run_tests.py unit

# Run integration tests only
python run_tests.py integration

# Run tests with coverage report
python run_tests.py coverage

# Run tests quickly (no coverage)
python run_tests.py quick
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_validation.py -v

# Run specific test method
pytest tests/unit/test_validation.py::TestInputSanitizer::test_sanitize_string_valid_input -v
```

## Test Categories

### Unit Tests

- **Input Validation (`test_validation.py`)**: Tests for input sanitization, SQL injection prevention, XSS prevention, bounds validation, and anomaly detection
- **Health Checks (`test_health.py`)**: Tests for ML model health, system resource monitoring, configuration validation, and startup checks
- **Authentication**: JWT token validation and user authentication flow
- **Rate Limiting**: Rate limit enforcement and configuration
- **Error Handling**: Custom exception classes and error responses

### Integration Tests

- **API Endpoints (`test_api_endpoints.py`)**: End-to-end testing of FastAPI endpoints including:
  - Authentication flow with JWT tokens
  - Request/response validation
  - Error handling and exception propagation
  - Rate limiting behavior
  - CORS and middleware functionality
  - Health check endpoints (basic and detailed)
  - Prediction endpoints with full validation pipeline

## Test Configuration

### pytest.ini
- Test discovery patterns
- Coverage configuration (80% minimum)
- Async test support
- Warning filters
- Test markers for categorization

### conftest.py Fixtures
- **mock_config**: Mock application configuration for testing
- **mock_models_dir**: Temporary directory with mock ML model files
- **mock_ml_service**: Mock ML service with prediction capabilities
- **valid_passenger_data**: Valid test data for passenger predictions
- **invalid_passenger_data**: Invalid test data for validation testing
- **mock_jwt_token**: Mock JWT token for authentication tests
- **app_client**: FastAPI async test client with all dependencies mocked
- **health_checker_mock**: Mock health checker for testing
- **mock_rate_limiter**: Mock rate limiter to avoid Redis dependency in tests

## Test Coverage

The test suite aims for comprehensive coverage of:

- **Input Validation**: 100% coverage of all validation rules and security checks
- **Health Monitoring**: All health check components and failure scenarios
- **API Endpoints**: All HTTP endpoints with success and error cases
- **Authentication**: JWT token validation and user authorization
- **Error Handling**: Custom exceptions and error response formatting
- **Configuration**: Application configuration loading and validation

## Mock Strategy

Tests use extensive mocking to:
- Isolate units under test from external dependencies
- Simulate various failure conditions
- Avoid requiring external services (Redis, databases)
- Speed up test execution
- Ensure deterministic test results

## Security Testing

Special focus on security-related testing:
- SQL injection prevention
- XSS attack prevention
- Input sanitization effectiveness
- Authentication bypass attempts
- Rate limiting enforcement

## Running in CI/CD

The test suite is designed to run in continuous integration environments:
- No external dependencies required
- Fast execution with mocking
- Comprehensive coverage reporting
- Clear failure reporting with detailed output

## Best Practices

- Tests are isolated and can run in any order
- Each test has a clear single responsibility
- Test names clearly describe what is being tested
- Fixtures are reusable across multiple test files
- Mock objects simulate realistic behavior
- Error cases are thoroughly tested
- Tests serve as documentation for expected behavior