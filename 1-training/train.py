"""
Titanic Survival Prediction - Production Training Pipeline

This script implements a production-ready ML training pipeline for the Titanic dataset.
It processes the raw data, trains multiple models, and saves all artifacts for production use.

Key Features:
- Data preprocessing with feature engineering
- Multiple model training (Logistic Regression & Decision Tree)
- Model persistence with all preprocessing components
- Reproducible results with fixed random seeds

Author: Titanic ML Predictor Platform
"""

import sys
import os

# Add parent directory to path before imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import pickle
import json
import warnings
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from shared.preprocessor import TitanicPreprocessor

warnings.filterwarnings('ignore')

# Configuration constants
RANDOM_STATE = 42
TEST_SIZE = 0.2
DATA_PATH = '../data/titanic passenger list.csv'
MODELS_DIR = '../models'


def load_data():
    """Load the Titanic dataset."""
    print(f"Loading data from {DATA_PATH}...")
    
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")
        
    df = pd.read_csv(DATA_PATH)
    print(f"Data loaded successfully. Shape: {df.shape}")
    print(f"Survival rate: {df['survived'].mean():.3f}")
    
    return df

def train_models(X_train, y_train):
    """Train machine learning models."""
    print("Training models...")
    
    # Logistic Regression
    print("Training Logistic Regression...")
    lr_model = LogisticRegression(random_state=RANDOM_STATE, max_iter=1000)
    lr_model.fit(X_train, y_train)
    
    # Decision Tree
    print("Training Decision Tree...")
    dt_model = DecisionTreeClassifier(
        random_state=RANDOM_STATE,
        max_depth=10,
        min_samples_split=20
    )
    dt_model.fit(X_train, y_train)
    
    print("Model training complete!")
    return lr_model, dt_model

def evaluate_models(models, X_test, y_test):
    """Evaluate trained models."""
    print("\nEvaluating models...")
    
    lr_model, dt_model = models
    results = {}
    
    # Evaluate Logistic Regression
    lr_pred = lr_model.predict(X_test)
    lr_accuracy = accuracy_score(y_test, lr_pred)
    results['logistic_regression'] = {
        'accuracy': lr_accuracy,
        'predictions': lr_pred
    }
    
    # Evaluate Decision Tree
    dt_pred = dt_model.predict(X_test)
    dt_accuracy = accuracy_score(y_test, dt_pred)
    results['decision_tree'] = {
        'accuracy': dt_accuracy,
        'predictions': dt_pred
    }
    
    # Ensemble prediction
    lr_proba = lr_model.predict_proba(X_test)[:, 1]
    dt_proba = dt_model.predict_proba(X_test)[:, 1]
    ensemble_proba = (lr_proba + dt_proba) / 2
    ensemble_pred = (ensemble_proba >= 0.5).astype(int)
    ensemble_accuracy = accuracy_score(y_test, ensemble_pred)
    
    results['ensemble'] = {
        'accuracy': ensemble_accuracy,
        'predictions': ensemble_pred
    }
    
    print(f"Logistic Regression Accuracy: {lr_accuracy:.3f}")
    print(f"Decision Tree Accuracy: {dt_accuracy:.3f}")
    print(f"Ensemble Accuracy: {ensemble_accuracy:.3f}")
    
    return results

def save_models(models, results):
    """Save trained models and evaluation results."""
    print(f"\nSaving models to {MODELS_DIR}/...")
    
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    lr_model, dt_model = models
    
    # Save models
    with open(f'{MODELS_DIR}/logistic_model.pkl', 'wb') as f:
        pickle.dump(lr_model, f)
        
    with open(f'{MODELS_DIR}/decision_tree_model.pkl', 'wb') as f:
        pickle.dump(dt_model, f)
    
    # Save evaluation results
    evaluation_results = {
        'logistic_regression_accuracy': results['logistic_regression']['accuracy'],
        'decision_tree_accuracy': results['decision_tree']['accuracy'],
        'ensemble_accuracy': results['ensemble']['accuracy']
    }
    
    with open(f'{MODELS_DIR}/evaluation_results.json', 'w') as f:
        json.dump(evaluation_results, f, indent=2)
    
    print("Model artifacts saved successfully!")

def main():
    """Main training pipeline."""
    print("🚢 TITANIC SURVIVAL PREDICTION - PRODUCTION TRAINING PIPELINE 🚢")
    print("=" * 80)
    
    try:
        # Load data
        df = load_data()
        
        # Initialize preprocessor
        preprocessor = TitanicPreprocessor()
        
        # Preprocess data
        df_processed = preprocessor.fit_transform(df)
        
        # Prepare features and target
        X = df_processed[preprocessor.get_feature_columns()]
        y = df_processed['survived']
        
        print(f"\nFeatures used: {preprocessor.get_feature_columns()}")
        print(f"Dataset shape: {X.shape}")
        
        # Split data
        print(f"\nSplitting data (test_size={TEST_SIZE})...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
        )
        
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        
        # Train models
        models = train_models(X_train, y_train)
        
        # Evaluate models
        results = evaluate_models(models, X_test, y_test)
        
        # Save models
        save_models(models, results)
        
        # Save preprocessor artifacts
        preprocessor.save_artifacts(MODELS_DIR)
        
        print("\n" + "=" * 80)
        print("🎉 TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("Model artifacts saved in the 'models/' directory:")
        print("- logistic_model.pkl")
        print("- decision_tree_model.pkl") 
        print("- label_encoders.pkl")
        print("- preprocessing_stats.json")
        print("- feature_columns.json")
        print("- evaluation_results.json")
        print("\nUse test_models.py to test the trained models interactively.")
        
    except Exception as e:
        print(f"❌ Error in training pipeline: {str(e)}")
        raise

if __name__ == "__main__":
    main()