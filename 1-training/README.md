# Training Pipeline

Machine learning model training pipeline for Titanic survival prediction using shared preprocessing components.

## Overview

This module contains the training pipeline that:
- Uses the shared `TitanicPreprocessor` for consistent data transformation
- Trains multiple ML models (Logistic Regression, Decision Tree)
- Evaluates model performance and generates metrics
- Saves trained models and artifacts for the API service

## Quick Start

```bash
# From project root
./doit.sh train

# Or directly
cd 1-training
python train.py
```

## Training Process

### 1. Data Loading
- Loads training data from `../data/titanic passenger list.csv`
- Handles missing data and basic validation

### 2. Preprocessing
- Uses shared `TitanicPreprocessor` class
- Feature engineering (age groups, fare categories, family size)
- Label encoding for categorical variables
- Consistent transformation pipeline used by API service

### 3. Model Training
- **Logistic Regression**: Linear model with regularization
- **Decision Tree**: Non-linear model with depth limiting
- Uses `RANDOM_STATE = 42` for reproducible results

### 4. Model Evaluation
- Train/test split for validation
- Accuracy scoring for both models
- Classification reports with precision, recall, F1-score
- Confusion matrices for detailed performance analysis

### 5. Artifact Generation
- **Model Files**: `logistic_model.pkl`, `decision_tree_model.pkl`
- **Preprocessor**: Label encoders and preprocessing statistics
- **Evaluation Results**: JSON file with model performance metrics
- **Feature Info**: Feature column names and transformations

## Output Files

Generated in `../models/` directory:
```
models/
├── logistic_model.pkl        # Trained logistic regression model
├── decision_tree_model.pkl   # Trained decision tree model  
├── label_encoders.pkl        # Label encoders for categorical features
├── feature_columns.json      # Ordered list of feature names
├── evaluation_results.json   # Model performance metrics
└── preprocessing_stats.json  # Feature statistics and transformations
```

## Configuration

Key training parameters in `train.py`:
```python
RANDOM_STATE = 42           # Reproducible results
TEST_SIZE = 0.2             # 20% held out for validation
MAX_DEPTH = 5               # Decision tree depth limit
MODELS_DIR = "../models"    # Output directory
```

## Model Performance

Typical performance metrics:
- **Logistic Regression**: ~80-82% accuracy
- **Decision Tree**: ~78-85% accuracy
- **Ensemble Average**: Often provides best results

## Integration with API Service

The trained models are automatically compatible with the FastAPI service:
- **Shared Preprocessor**: Ensures consistent data transformation
- **Model Loading**: API service loads models from `../models/`
- **Feature Compatibility**: Same feature engineering pipeline
- **Prediction Format**: Compatible prediction output structure

## Dependencies

Uses consolidated project dependencies from `../requirements.txt`:
- `pandas`, `numpy` for data manipulation
- `scikit-learn` for ML models and evaluation
- `pickle` for model serialization
- Shared `TitanicPreprocessor` component

## Troubleshooting

### Common Issues

**Missing Data Files**:
```bash
# Ensure training data exists
ls ../data/"titanic passenger list.csv"
```

**Import Errors**:
```bash
# Install dependencies
pip install -r ../requirements.txt
```

**Model Directory Permissions**:
```bash
# Create models directory if missing
mkdir -p ../models
```

### Validation

Verify successful training:
```bash
# Check generated files
ls -la ../models/
# Should see .pkl and .json files

# Validate model loading (from 2-ml-service)
cd ../2-ml-service
python -c "
import asyncio
from app.services.ml_service import MLService
service = MLService()
asyncio.run(service.load_models())
print('✅ Models load successfully')
"
```