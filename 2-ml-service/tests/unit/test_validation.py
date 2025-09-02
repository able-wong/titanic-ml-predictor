"""
Unit tests for input validation and sanitization module.

Tests comprehensive input validation including:
- String sanitization and security checks
- Numeric bounds validation
- Categorical value validation
- Anomaly detection
- SQL injection prevention
- XSS prevention
"""

import pytest
from unittest.mock import patch

from app.utils.validation import (
    InputSanitizer,
    validate_passenger_input,
    validate_query_parameters,
)
from app.core.exceptions import ValidationError


class TestInputSanitizer:
    """Test the InputSanitizer class methods."""

    @pytest.fixture
    def sanitizer(self):
        """Create InputSanitizer instance for testing."""
        return InputSanitizer()

    def test_sanitize_string_valid_input(self, sanitizer):
        """Test string sanitization with valid input."""
        result = sanitizer.sanitize_string("male", "sex")
        assert result == "male"

        result = sanitizer.sanitize_string("  female  ", "sex")
        assert result == "female"

    def test_sanitize_string_html_escape(self, sanitizer):
        """Test HTML escaping in string sanitization."""
        # Should raise ValidationError due to XSS pattern
        with pytest.raises(ValidationError) as exc_info:
            sanitizer.sanitize_string("<script>alert('xss')</script>", "test_field")

        assert "invalid_characters" in str(exc_info.value.details)

    def test_sanitize_string_sql_injection(self, sanitizer):
        """Test SQL injection prevention."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "'; DELETE FROM users; --",
        ]

        for malicious_input in malicious_inputs:
            with pytest.raises(ValidationError) as exc_info:
                sanitizer.sanitize_string(malicious_input, "test_field")

            assert exc_info.value.details["issue"] == "invalid_characters"

    def test_sanitize_string_xss_prevention(self, sanitizer):
        """Test XSS prevention."""
        xss_inputs = [
            "<script>malicious()</script>",
            "<iframe src='evil.com'></iframe>",
            "javascript:alert('xss')",
            "<object data='malware.swf'></object>",
            "onclick='bad()'",
        ]

        for xss_input in xss_inputs:
            with pytest.raises(ValidationError):
                sanitizer.sanitize_string(xss_input, "test_field")

    def test_sanitize_string_suspicious_chars(self, sanitizer):
        """Test removal of suspicious control characters."""
        with pytest.raises(ValidationError):
            sanitizer.sanitize_string("test\x00\x01\x1f", "test_field")

    def test_sanitize_string_excessive_whitespace(self, sanitizer):
        """Test handling of excessive whitespace."""
        result = sanitizer.sanitize_string(
            "test          with     spaces", "test_field"
        )
        assert "          " not in result
        assert (
            result == "test with     spaces"
        )  # Regex only removes 10+ consecutive spaces

    def test_sanitize_string_length_validation(self, sanitizer):
        """Test string length validation."""
        # Test empty string after sanitization
        with pytest.raises(ValidationError) as exc_info:
            sanitizer.sanitize_string("   ", "test_field")

        assert "empty_after_sanitization" in str(exc_info.value.details)

        # Test overly long string
        long_string = "a" * 101
        with pytest.raises(ValidationError) as exc_info:
            sanitizer.sanitize_string(long_string, "test_field")

        assert exc_info.value.details["max_length"] == 100

    def test_sanitize_string_non_string_input(self, sanitizer):
        """Test validation error for non-string input."""
        with pytest.raises(ValidationError) as exc_info:
            sanitizer.sanitize_string(123, "test_field")

        assert exc_info.value.details["received_type"] == "int"

    def test_validate_numeric_bounds_valid(self, sanitizer):
        """Test numeric bounds validation with valid values."""
        # Test age bounds
        assert sanitizer.validate_numeric_bounds(25, "age") == 25
        assert sanitizer.validate_numeric_bounds(0, "age") == 0
        assert sanitizer.validate_numeric_bounds(120, "age") == 120

        # Test fare bounds
        assert sanitizer.validate_numeric_bounds(50.5, "fare") == 50.5

    def test_validate_numeric_bounds_out_of_range(self, sanitizer):
        """Test numeric bounds validation with out-of-range values."""
        # Age too high
        with pytest.raises(ValidationError) as exc_info:
            sanitizer.validate_numeric_bounds(150, "age")

        assert exc_info.value.details["field"] == "age"
        assert exc_info.value.details["max"] == 120

        # Age too low
        with pytest.raises(ValidationError):
            sanitizer.validate_numeric_bounds(-5, "age")

        # Fare too low
        with pytest.raises(ValidationError):
            sanitizer.validate_numeric_bounds(-10, "fare")

    def test_validate_numeric_bounds_outlier_detection(self, sanitizer, caplog):
        """Test outlier detection for suspicious but valid values."""
        # This should not raise an error but should log a warning
        result = sanitizer.validate_numeric_bounds(85, "age")
        assert result == 85

        # Check if warning was logged (would need proper logging setup)

    def test_validate_categorical_valid(self, sanitizer):
        """Test categorical validation with valid values."""
        assert sanitizer.validate_categorical("male", "sex") == "male"
        assert sanitizer.validate_categorical("female", "sex") == "female"
        assert sanitizer.validate_categorical("C", "embarked") == "C"
        assert sanitizer.validate_categorical(1, "pclass") == 1

    def test_validate_categorical_invalid(self, sanitizer):
        """Test categorical validation with invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            sanitizer.validate_categorical("other", "sex")

        assert "male" in str(exc_info.value.details["valid_values"])
        assert "female" in str(exc_info.value.details["valid_values"])

        with pytest.raises(ValidationError):
            sanitizer.validate_categorical("X", "embarked")

        with pytest.raises(ValidationError):
            sanitizer.validate_categorical(4, "pclass")

    def test_detect_anomalies_normal_data(self, sanitizer):
        """Test anomaly detection with normal passenger data."""
        normal_data = {
            "pclass": 2,
            "sex": "male",
            "age": 30,
            "sibsp": 1,
            "parch": 0,
            "fare": 50.0,
        }

        anomalies = sanitizer.detect_anomalies(normal_data)
        assert len(anomalies) == 0

    def test_detect_anomalies_suspicious_patterns(self, sanitizer):
        """Test anomaly detection with suspicious patterns."""
        # Child with high fare
        child_high_fare = {"pclass": 1, "age": 8, "fare": 200.0, "sibsp": 0, "parch": 2}

        anomalies = sanitizer.detect_anomalies(child_high_fare)
        assert "child_high_fare" in anomalies

        # Large family size
        large_family = {"sibsp": 6, "parch": 5, "age": 35, "pclass": 3}

        anomalies = sanitizer.detect_anomalies(large_family)
        assert "large_family_size" in anomalies

        # First class low fare
        first_class_cheap = {"pclass": 1, "fare": 5.0, "age": 25}

        anomalies = sanitizer.detect_anomalies(first_class_cheap)
        assert "first_class_low_fare" in anomalies

        # Third class high fare
        third_class_expensive = {"pclass": 3, "fare": 150.0, "age": 40}

        anomalies = sanitizer.detect_anomalies(third_class_expensive)
        assert "third_class_high_fare" in anomalies

    def test_sanitize_and_validate_success(self, sanitizer):
        """Test complete sanitization and validation with valid data."""
        input_data = {
            "pclass": 1,
            "sex": "female",
            "age": 25.0,
            "sibsp": 0,
            "parch": 0,
            "fare": 100.0,
            "embarked": "S",
        }

        result = sanitizer.sanitize_and_validate(input_data)

        assert result["pclass"] == 1
        assert result["sex"] == "female"
        assert result["age"] == 25.0
        assert result["embarked"] == "S"

    def test_sanitize_and_validate_type_conversion(self, sanitizer):
        """Test type conversion during validation."""
        input_data = {
            "pclass": "2",  # String should convert to int
            "age": "25.5",  # String should convert to float
            "sibsp": 1.0,  # Float should convert to int
            "sex": "male",
            "fare": 50,  # Int should remain/convert to float
            "embarked": "C",
        }

        result = sanitizer.sanitize_and_validate(input_data)

        assert isinstance(result["pclass"], int)
        assert result["pclass"] == 2
        assert isinstance(result["age"], float)
        assert result["age"] == 25.5
        assert isinstance(result["sibsp"], int)
        assert result["sibsp"] == 1

    def test_sanitize_and_validate_failure(self, sanitizer):
        """Test validation failure with invalid data."""
        invalid_data = {
            "pclass": 5,  # Invalid class
            "sex": "other",  # Invalid sex
            "age": -5,  # Invalid age
            "fare": -10,  # Invalid fare
        }

        with pytest.raises(ValidationError):
            sanitizer.sanitize_and_validate(invalid_data)

    @patch("app.utils.validation.logger")
    def test_sanitize_and_validate_logging(self, mock_logger, sanitizer):
        """Test that validation logging works correctly."""
        # Test with anomalous but valid data
        anomalous_data = {
            "pclass": 3,
            "sex": "male",
            "age": 10,
            "fare": 200.0,  # Child with high fare
            "sibsp": 0,
            "parch": 0,
            "embarked": "S",
        }

        # Call the method but don't need to use the result
        # We're testing that it logs anomalies, not the result
        sanitizer.sanitize_and_validate(anomalous_data)

        # Verify logging calls
        mock_logger.info.assert_called()
        mock_logger.debug.assert_called()


class TestValidationFunctions:
    """Test module-level validation functions."""

    def test_validate_passenger_input_success(self, valid_passenger_data):
        """Test successful passenger input validation."""
        result = validate_passenger_input(valid_passenger_data)

        assert result["pclass"] == valid_passenger_data["pclass"]
        assert result["sex"] == valid_passenger_data["sex"]
        assert result["age"] == valid_passenger_data["age"]

    def test_validate_passenger_input_failure(self, invalid_passenger_data):
        """Test passenger input validation failures."""
        for invalid_data in invalid_passenger_data:
            with pytest.raises(ValidationError):
                validate_passenger_input(invalid_data)

    def test_validate_query_parameters_success(self):
        """Test successful query parameter validation."""
        params = {"detailed": "true", "format": "json"}

        result = validate_query_parameters(params)

        assert result["detailed"] == "true"
        assert result["format"] == "json"

    def test_validate_query_parameters_malicious(self):
        """Test query parameter validation with malicious input."""
        malicious_params = {
            "detailed": "true'; DROP TABLE users; --",
            "format": "<script>alert('xss')</script>",
        }

        with pytest.raises(ValidationError):
            validate_query_parameters(malicious_params)

    def test_validate_query_parameters_non_string(self):
        """Test query parameter validation with non-string values."""
        params = {
            "detailed": True,  # Boolean should pass through
            "count": 10,  # Integer should pass through
            "name": "test",  # String should be validated
        }

        result = validate_query_parameters(params)

        assert result["detailed"] is True
        assert result["count"] == 10
        assert result["name"] == "test"
