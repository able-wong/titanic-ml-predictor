"""
Advanced input validation and sanitization module.

This module provides comprehensive input validation, sanitization, and security
checks beyond basic Pydantic validation to ensure data integrity and prevent
security vulnerabilities.
"""

import re
import html
import unicodedata
from typing import Dict, Any, List, Union

from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger

logger = get_logger("validation")


class InputSanitizer:
    """
    Advanced input sanitization and validation for ML service.
    
    Provides defense-in-depth input validation including:
    - Data type validation and coercion
    - Range and boundary validation
    - Format validation and normalization
    - SQL injection prevention
    - XSS prevention
    - Unicode normalization
    - Anomaly detection
    """
    
    def __init__(self):
        # Precompiled regex patterns for efficiency
        self.patterns = {
            'sql_injection': re.compile(
                r'(\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b|'
                r'[\'";]|--|\*|/\*|\*/)', 
                re.IGNORECASE
            ),
            'xss_patterns': re.compile(
                r'(<script|<iframe|<object|<embed|javascript:|vbscript:|on\w+\s*=)', 
                re.IGNORECASE
            ),
            'suspicious_chars': re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]'),
            'excessive_whitespace': re.compile(r'\s{10,}'),  # 10+ consecutive spaces
        }
        
        # Define realistic bounds for Titanic dataset
        self.bounds = {
            'age': {'min': 0, 'max': 120, 'typical_max': 80},
            'fare': {'min': 0, 'max': 1000, 'typical_max': 500},
            'sibsp': {'min': 0, 'max': 20, 'typical_max': 8},  # Historical max was 8
            'parch': {'min': 0, 'max': 20, 'typical_max': 9}   # Historical max was 9
        }
        
        # Valid categorical values
        self.valid_categories = {
            'sex': {'male', 'female'},
            'embarked': {'C', 'Q', 'S'},
            'pclass': {1, 2, 3}
        }
    
    def sanitize_string(self, value: str, field_name: str) -> str:
        """
        Comprehensive string sanitization.
        
        Args:
            value: String value to sanitize
            field_name: Name of the field for logging
            
        Returns:
            Sanitized string
            
        Raises:
            ValidationError: If string contains malicious content
        """
        if not isinstance(value, str):
            raise ValidationError(
                message=f"Field '{field_name}' must be a string",
                details={"field": field_name, "received_type": type(value).__name__}
            )
        
        original_value = value
        
        # 1. Remove null bytes and control characters
        if self.patterns['suspicious_chars'].search(value):
            logger.warning(
                "Suspicious characters detected in input",
                field=field_name,
                original_length=len(value)
            )
            raise ValidationError(
                message=f"Field '{field_name}' contains invalid characters",
                details={"field": field_name, "issue": "control_characters"}
            )
        
        # 2. Check for SQL injection patterns
        if self.patterns['sql_injection'].search(value):
            logger.warning(
                "SQL injection attempt detected",
                field=field_name,
                pattern_matched=True
            )
            raise ValidationError(
                message=f"Field '{field_name}' contains invalid content",
                details={"field": field_name, "issue": "invalid_characters"}
            )
        
        # 3. Check for XSS patterns
        if self.patterns['xss_patterns'].search(value):
            logger.warning(
                "XSS attempt detected",
                field=field_name,
                pattern_matched=True
            )
            raise ValidationError(
                message=f"Field '{field_name}' contains invalid content",
                details={"field": field_name, "issue": "invalid_characters"}
            )
        
        # 4. Normalize Unicode
        value = unicodedata.normalize('NFKC', value)
        
        # 5. HTML escape for safety
        value = html.escape(value)
        
        # 6. Strip excessive whitespace but preserve single spaces
        value = self.patterns['excessive_whitespace'].sub(' ', value)
        value = value.strip()
        
        # 7. Check length bounds
        if len(value) == 0:
            raise ValidationError(
                message=f"Field '{field_name}' cannot be empty after sanitization",
                details={"field": field_name, "issue": "empty_after_sanitization"}
            )
        
        if len(value) > 100:  # Reasonable upper bound
            logger.warning(
                "Unusually long string input",
                field=field_name,
                length=len(value),
                original_length=len(original_value)
            )
            raise ValidationError(
                message=f"Field '{field_name}' is too long",
                details={"field": field_name, "max_length": 100, "actual_length": len(value)}
            )
        
        return value
    
    def validate_numeric_bounds(self, value: Union[int, float], field_name: str) -> Union[int, float]:
        """
        Validate numeric values with bounds checking and anomaly detection.
        
        Args:
            value: Numeric value to validate
            field_name: Name of the field for logging
            
        Returns:
            Validated numeric value
            
        Raises:
            ValidationError: If value is out of bounds or suspicious
        """
        if field_name not in self.bounds:
            return value  # No specific bounds defined
        
        bounds = self.bounds[field_name]
        
        # Check hard bounds
        if value < bounds['min'] or value > bounds['max']:
            raise ValidationError(
                message=f"Field '{field_name}' is out of valid range",
                details={
                    "field": field_name,
                    "value": value,
                    "min": bounds['min'],
                    "max": bounds['max']
                }
            )
        
        # Check for suspicious values (outliers)
        if value > bounds.get('typical_max', bounds['max']):
            logger.info(
                "Unusual value detected",
                field=field_name,
                value=value,
                typical_max=bounds['typical_max'],
                severity="outlier"
            )
        
        return value
    
    def validate_categorical(self, value: Any, field_name: str) -> Any:
        """
        Validate categorical values.
        
        Args:
            value: Value to validate
            field_name: Name of the field
            
        Returns:
            Validated value
            
        Raises:
            ValidationError: If value is not in valid categories
        """
        if field_name not in self.valid_categories:
            return value  # No validation rules defined
        
        valid_values = self.valid_categories[field_name]
        
        if value not in valid_values:
            raise ValidationError(
                message=f"Field '{field_name}' has invalid value",
                details={
                    "field": field_name,
                    "value": value,
                    "valid_values": list(valid_values)
                }
            )
        
        return value
    
    def detect_anomalies(self, passenger_data: Dict[str, Any]) -> List[str]:
        """
        Detect potential anomalies in passenger data.
        
        Args:
            passenger_data: Dictionary of passenger data
            
        Returns:
            List of anomaly descriptions
        """
        anomalies = []
        
        # Check for logical inconsistencies
        if passenger_data.get('age', 0) < 16 and passenger_data.get('parch', 0) > 0:
            # Child with parents/children - could be valid but worth noting
            pass
        
        # Check age vs fare relationship (very rough heuristic)
        age = passenger_data.get('age', 0)
        fare = passenger_data.get('fare', 0)
        
        if age < 12 and fare > 100:
            anomalies.append("child_high_fare")
        
        # Check family size consistency
        sibsp = passenger_data.get('sibsp', 0)
        parch = passenger_data.get('parch', 0)
        family_size = sibsp + parch + 1
        
        if family_size > 10:
            anomalies.append("large_family_size")
        
        # Check fare vs class consistency
        pclass = passenger_data.get('pclass', 3)
        fare = passenger_data.get('fare', 0)
        
        # Very rough fare expectations by class
        if pclass == 1 and fare < 20:
            anomalies.append("first_class_low_fare")
        elif pclass == 3 and fare > 100:
            anomalies.append("third_class_high_fare")
        
        return anomalies
    
    def sanitize_and_validate(self, passenger_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive sanitization and validation of passenger data.
        
        Args:
            passenger_data: Raw passenger data dictionary
            
        Returns:
            Sanitized and validated passenger data
            
        Raises:
            ValidationError: If validation fails
        """
        sanitized_data = {}
        
        try:
            # Sanitize string fields
            for field in ['sex', 'embarked']:
                if field in passenger_data:
                    sanitized_value = self.sanitize_string(
                        str(passenger_data[field]), 
                        field
                    )
                    sanitized_data[field] = sanitized_value
            
            # Validate and sanitize numeric fields
            numeric_fields = ['pclass', 'age', 'sibsp', 'parch', 'fare']
            for field in numeric_fields:
                if field in passenger_data:
                    value = passenger_data[field]
                    
                    # Ensure numeric type
                    if field == 'pclass' or field in ['sibsp', 'parch']:
                        # Integer fields
                        if not isinstance(value, int):
                            try:
                                value = int(float(value))  # Handle "2.0" -> 2
                            except (ValueError, TypeError):
                                raise ValidationError(
                                    message=f"Field '{field}' must be an integer",
                                    details={"field": field, "value": value}
                                )
                    else:
                        # Float fields
                        if not isinstance(value, (int, float)):
                            try:
                                value = float(value)
                            except (ValueError, TypeError):
                                raise ValidationError(
                                    message=f"Field '{field}' must be numeric",
                                    details={"field": field, "value": value}
                                )
                    
                    # Validate bounds
                    validated_value = self.validate_numeric_bounds(value, field)
                    sanitized_data[field] = validated_value
            
            # Validate categorical fields
            for field in ['sex', 'embarked', 'pclass']:
                if field in sanitized_data:
                    sanitized_data[field] = self.validate_categorical(
                        sanitized_data[field], 
                        field
                    )
            
            # Detect and log anomalies
            anomalies = self.detect_anomalies(sanitized_data)
            if anomalies:
                logger.info(
                    "Data anomalies detected",
                    anomalies=anomalies,
                    passenger_data=sanitized_data,
                    severity="info"
                )
            
            logger.debug(
                "Input validation completed successfully",
                fields_validated=len(sanitized_data),
                anomalies_detected=len(anomalies)
            )
            
            return sanitized_data
            
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(
                "Unexpected error during validation",
                error_type=type(e).__name__,
                error_message=str(e)
            )
            raise ValidationError(
                message="Input validation failed",
                details={"error": str(e)}
            )


# Global sanitizer instance
input_sanitizer = InputSanitizer()


def validate_passenger_input(passenger_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main validation function for passenger data.
    
    Args:
        passenger_data: Raw passenger data from API request
        
    Returns:
        Sanitized and validated passenger data
        
    Raises:
        ValidationError: If validation fails
    """
    return input_sanitizer.sanitize_and_validate(passenger_data)


def validate_query_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate query parameters to prevent injection attacks.
    
    Args:
        params: Dictionary of query parameters
        
    Returns:
        Validated query parameters
        
    Raises:
        ValidationError: If validation fails
    """
    validated_params = {}
    
    for key, value in params.items():
        if isinstance(value, str):
            # Basic sanitization for query params
            sanitized_value = input_sanitizer.sanitize_string(value, key)
            validated_params[key] = sanitized_value
        else:
            validated_params[key] = value
    
    return validated_params