# Training Pipeline - Titanic Survival Prediction

This directory contains the production training pipeline for the Titanic ML Predictor Platform. It processes the Titanic dataset, trains machine learning models, and generates production-ready model artifacts.

## Overview

The training pipeline implements:
- **Data Processing**: Cleans and preprocesses the Titanic dataset with feature engineering
- **Model Training**: Trains Logistic Regression and Decision Tree algorithms  
- **Model Persistence**: Saves all trained models and preprocessing components
- **Interactive Testing**: CLI tool for validating model predictions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Train Models

```bash
python train.py
```

This will:
- Load data from `../data/titanic passenger list.csv`
- Process and split the data (80/20 train/test)
- Train Logistic Regression and Decision Tree models
- Save all model artifacts to the project root `../models/` directory
- Display training results and accuracy metrics

### 3. Test Models

```bash
python test_models.py
```

Interactive CLI tool that allows you to:
- Input passenger information manually
- Get survival predictions from individual models
- See ensemble prediction results
- View confidence levels for predictions

## Generated Model Artifacts

After running `train.py`, the following files are created in the project root `../models/` directory:

- **`logistic_model.pkl`** - Trained Logistic Regression model
- **`decision_tree_model.pkl`** - Trained Decision Tree model  
- **`label_encoders.pkl`** - Encoders for categorical variables (sex, embarked)
- **`preprocessing_stats.json`** - Statistics for handling missing values
- **`feature_columns.json`** - Ordered list of feature columns
- **`evaluation_results.json`** - Model accuracy and performance metrics

## Data Processing Pipeline

### Data Cleaning
- Removes unnecessary columns (name, ticket, cabin, boat, body, home.dest)
- Handles missing values:
  - Age: filled with median
  - Embarked: filled with mode (most common value)
  - Fare: filled with median

### Feature Engineering
- **family_size**: Total family members aboard (siblings + spouses + parents + children + 1)
- **is_alone**: Binary indicator for passengers traveling alone
- **age_group**: Age categories (Child: 0-17, Young Adult: 18-34, Adult: 35-59, Senior: 60+)

### Encoding
- **sex**: male=1, female=0
- **embarked**: C/Q/S encoded to numeric values

## Model Architecture

### Algorithms Used
1. **Logistic Regression**: Interpretable linear model for baseline performance
2. **Decision Tree**: Non-linear model to capture complex patterns
3. **Ensemble**: Averages probabilities from both models for final prediction

### Model Parameters
- **Logistic Regression**: `random_state=42, max_iter=1000`
- **Decision Tree**: `random_state=42, max_depth=10, min_samples_split=20`

## Example Usage

### Training Output
```
🚢 TITANIC SURVIVAL PREDICTION - PRODUCTION TRAINING PIPELINE 🚢
===============================================================================
Loading data from ../data/titanic passenger list.csv...
Data loaded successfully. Shape: (1309, 14)
Survival rate: 0.381

Starting data preprocessing...
Handling missing values...
Creating engineered features...
Encoding categorical variables...
Preprocessing complete. Final shape: (1309, 11)

Features used: ['pclass', 'sex', 'age', 'sibsp', 'parch', 'fare', 'embarked', 'family_size', 'is_alone', 'age_group']
Dataset shape: (1309, 10)

Splitting data (test_size=0.2)...
Training set: 1047 samples
Test set: 262 samples

Training models...
Training Logistic Regression...
Training Decision Tree...
Model training complete!

Evaluating models...
Logistic Regression Accuracy: 0.817
Decision Tree Accuracy: 0.809
Ensemble Accuracy: 0.821

Saving models to models/...
All model artifacts saved successfully!

===============================================================================
🎉 TRAINING PIPELINE COMPLETED SUCCESSFULLY!
===============================================================================
```

### Testing Interface
```bash
$ python test_models.py

🚢 TITANIC SURVIVAL PREDICTION - MODEL TESTING CLI 🚢
===============================================================================

ENTER PASSENGER INFORMATION
===============================================================================
Passenger Class (1=First, 2=Second, 3=Third): 1
Sex (male/female): female  
Age (years): 25
Siblings/Spouses aboard: 0
Parents/Children aboard: 0
Fare paid: 50.0
Embarked (C=Cherbourg, Q=Queenstown, S=Southampton): S

PREDICTION RESULTS
===============================================================================
Logistic Regression:
  Survival Probability: 0.892 (89.2%)
  Prediction: SURVIVED

Decision Tree:
  Survival Probability: 0.847 (84.7%)
  Prediction: SURVIVED

🎯 ENSEMBLE PREDICTION:
  Survival Probability: 0.869 (86.9%)
  Final Prediction: ✅ SURVIVED
  Confidence Level: High (0.739)
```

## Technical Specifications

- **Python**: 3.9+ compatibility
- **Random State**: Fixed at 42 for reproducible results
- **Train/Test Split**: 80/20 with stratification
- **Missing Value Strategy**: Median for numeric, mode for categorical
- **Feature Selection**: Automated based on preprocessing pipeline
- **Model Serialization**: Pickle format for Python compatibility

## Integration with ML Service

The generated model artifacts are designed to be consumed by the ML Service component:
- All preprocessing logic is saved and reusable
- Models are serialized in a consistent format
- Feature ordering is preserved for prediction consistency
- Evaluation metrics are available for monitoring

## Error Handling

The pipeline includes comprehensive error handling for:
- Missing data files
- Invalid data formats  
- Model training failures
- File I/O operations
- User input validation (in testing tool)

## Next Steps

After training models:
1. Use the generated artifacts in the ML Service (`2-ml-service/`)
2. Deploy models to production environment
3. Monitor model performance and retrain as needed
4. Implement A/B testing for model improvements