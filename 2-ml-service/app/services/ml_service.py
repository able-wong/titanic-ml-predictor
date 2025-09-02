"""
Machine Learning Service for Titanic Survival Predictions.

This module contains the ML service class that handles model loading,
preprocessing, and prediction logic. It adapts the proven patterns from
api_example.py for production use with FastAPI.
"""

import os
import pickle
import json
import sys
from typing import Dict, Any

# Add project root to path for shared imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.preprocessor import TitanicPreprocessor
from app.models import PredictionResponse, ModelPrediction, EnsemblePrediction
from app.core.exceptions import ModelNotLoadedError, PredictionError, ConfigurationError
from app.core.logging_config import get_logger


class MLService:
    """
    Production ML service for Titanic survival predictions.
    
    This class handles model loading, preprocessing, and prediction logic
    using the shared models and preprocessor from the training pipeline.
    """
    
    def __init__(self, models_dir: str = "../models"):
        """Initialize the ML service with model directory path."""
        self.models_dir = models_dir
        self.preprocessor = None
        self.lr_model = None
        self.dt_model = None
        self.model_accuracy = {}
        self.is_loaded = False
        self.logger = get_logger("ml_service")
        
    async def load_models(self) -> None:
        """
        Load all models and preprocessor artifacts asynchronously.
        
        This method should be called once during application startup.
        
        Raises:
            FileNotFoundError: If model files are not found
            Exception: If models fail to load
        """
        self.logger.info(
            "Starting ML service initialization",
            models_dir=self.models_dir,
            initialization_phase="starting"
        )
        
        if not os.path.exists(self.models_dir):
            raise ConfigurationError(
                f"Models directory '{self.models_dir}' not found",
                details={"models_dir": self.models_dir, "suggestion": "Run the training pipeline first"}
            )
        
        try:
            # Load preprocessor
            self.logger.info(
                "Loading preprocessor artifacts",
                models_dir=self.models_dir,
                initialization_phase="preprocessor"
            )
            self.preprocessor = TitanicPreprocessor.load_artifacts(self.models_dir)
            
            # Load trained models
            self.logger.info(
                "Loading trained models",
                initialization_phase="models"
            )
            with open(os.path.join(self.models_dir, 'logistic_model.pkl'), 'rb') as f:
                self.lr_model = pickle.load(f)
                
            with open(os.path.join(self.models_dir, 'decision_tree_model.pkl'), 'rb') as f:
                self.dt_model = pickle.load(f)
                
            # Load evaluation results for health checks
            eval_results_path = os.path.join(self.models_dir, 'evaluation_results.json')
            if os.path.exists(eval_results_path):
                self.logger.info(
                    "Loading model evaluation results",
                    initialization_phase="evaluation_results"
                )
                with open(eval_results_path, 'r') as f:
                    eval_results = json.load(f)
                    self.model_accuracy = {
                        "logistic_regression": eval_results.get("logistic_regression_accuracy", 0.0),
                        "decision_tree": eval_results.get("decision_tree_accuracy", 0.0),
                        "ensemble": eval_results.get("ensemble_accuracy", 0.0)
                    }
            else:
                self.logger.warning(
                    "Evaluation results file not found",
                    eval_results_path=eval_results_path,
                    initialization_phase="evaluation_results"
                )
            
            self.is_loaded = True
            self.logger.info(
                "ML service initialization completed successfully",
                initialization_phase="completed",
                feature_columns=self.preprocessor.get_feature_columns(),
                model_accuracy=self.model_accuracy,
                models_loaded=True
            )
            
        except ConfigurationError:
            raise
        except Exception as e:
            self.logger.error(
                "Failed to load ML service",
                initialization_phase="failed",
                error_type=type(e).__name__,
                error_message=str(e),
                models_dir=self.models_dir
            )
            raise ModelNotLoadedError(
                "Failed to load ML models",
                details={"original_error": str(e), "models_dir": self.models_dir}
            )
    
    def is_healthy(self) -> Dict[str, Any]:
        """
        Get health status of the ML service.
        
        Returns:
            Dict containing service health information
        """
        return {
            "status": "healthy" if self.is_loaded else "unhealthy",
            "models_loaded": self.is_loaded,
            "preprocessor_ready": self.preprocessor is not None,
            "model_accuracy": self.model_accuracy if self.is_loaded else None
        }
    
    async def predict_survival(self, passenger_data: Dict[str, Any]) -> PredictionResponse:
        """
        Predict survival probability for a passenger.
        
        Args:
            passenger_data (Dict): Passenger information dictionary
            
        Returns:
            PredictionResponse: Complete prediction results with individual and ensemble predictions
            
        Raises:
            RuntimeError: If models are not loaded
            Exception: If prediction fails
        """
        if not self.is_loaded:
            raise ModelNotLoadedError("Models not loaded. Service initialization failed.")
        
        try:
            self.logger.debug(
                "Starting prediction process",
                prediction_phase="preprocessing"
            )
            
            # Preprocess passenger data using shared preprocessor
            features = self.preprocessor.preprocess_single_passenger(passenger_data)
            
            self.logger.debug(
                "Preprocessing completed",
                prediction_phase="model_inference",
                feature_shape=features.shape if hasattr(features, 'shape') else None
            )
            
            # Get predictions from both models
            lr_prob = self.lr_model.predict_proba(features)[0, 1]
            dt_prob = self.dt_model.predict_proba(features)[0, 1]
            
            # Ensemble prediction (average)
            ensemble_prob = (lr_prob + dt_prob) / 2
            
            # Calculate confidence (distance from decision boundary)
            confidence = abs(ensemble_prob - 0.5) * 2
            
            # Determine confidence level
            if confidence > 0.7:
                confidence_level = "high"
            elif confidence > 0.4:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            self.logger.debug(
                "Model inference completed",
                prediction_phase="result_formatting",
                logistic_regression_prob=round(lr_prob, 3),
                decision_tree_prob=round(dt_prob, 3),
                ensemble_prob=round(ensemble_prob, 3),
                confidence=round(confidence, 3),
                confidence_level=confidence_level
            )
            
            # Create individual model predictions
            individual_models = {
                "logistic_regression": ModelPrediction(
                    probability=round(lr_prob, 3),
                    prediction="survived" if lr_prob >= 0.5 else "did_not_survive"
                ),
                "decision_tree": ModelPrediction(
                    probability=round(dt_prob, 3),
                    prediction="survived" if dt_prob >= 0.5 else "did_not_survive"
                )
            }
            
            # Create ensemble prediction
            ensemble_result = EnsemblePrediction(
                probability=round(ensemble_prob, 3),
                prediction="survived" if ensemble_prob >= 0.5 else "did_not_survive",
                confidence=round(confidence, 3),
                confidence_level=confidence_level
            )
            
            return PredictionResponse(
                individual_models=individual_models,
                ensemble_result=ensemble_result
            )
            
        except ModelNotLoadedError:
            raise
        except Exception as e:
            self.logger.error(
                "Prediction generation failed",
                prediction_phase="failed",
                error_type=type(e).__name__,
                error_message=str(e),
                passenger_data=passenger_data
            )
            raise PredictionError(
                f"Failed to generate prediction: {str(e)}",
                details={"original_error": str(e), "passenger_data": passenger_data}
            )
    
    def get_feature_columns(self) -> list:
        """
        Get the list of feature columns used by the models.
        
        Returns:
            List of feature column names
        """
        if not self.is_loaded or not self.preprocessor:
            return []
        
        return self.preprocessor.get_feature_columns()


# Global ML service instance (initialized at startup)
ml_service = MLService()