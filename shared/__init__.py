"""
Shared components for the Titanic ML Predictor Platform.

This package contains common code that is shared across different components
of the platform, including the training pipeline and ML API service.

Components:
- preprocessor: Data preprocessing and feature engineering logic
"""

from .preprocessor import TitanicPreprocessor, create_passenger_dataframe

__version__ = "1.0.0"
__author__ = "Titanic ML Predictor Platform"

__all__ = ["TitanicPreprocessor", "create_passenger_dataframe"]
