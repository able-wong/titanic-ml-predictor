# Shared Components - Titanic ML Predictor Platform

This directory contains shared code that is used across multiple components of the Titanic ML Predictor Platform, ensuring consistent behavior between training and production inference.

## Overview

The shared components provide:
- **Consistent Preprocessing**: Same data transformations in training and ML API
- **Reusable Logic**: Avoid code duplication across components
- **Production Ready**: Proper error handling and artifact management
- **Type Safety**: Well-defined interfaces and documentation

## Components

### TitanicPreprocessor (`preprocessor.py`)

The core preprocessing class that handles all data transformations for the Titanic dataset.

#### Key Features
- **Fit/Transform Pattern**: Follows scikit-learn conventions
- **Missing Value Handling**: Consistent strategies across training/inference
- **Feature Engineering**: Family size, age groups, travel alone indicators
- **Categorical Encoding**: Label encoders with unseen category handling
- **Artifact Persistence**: Save/load preprocessing parameters
- **Single Passenger Support**: Optimized for API inference

#### Usage Example

```python
from shared.preprocessor import TitanicPreprocessor

# Training usage
preprocessor = TitanicPreprocessor()
df_processed = preprocessor.fit_transform(training_df)

# Save for production use
preprocessor.save_artifacts('models/')

# Production/inference usage
preprocessor = TitanicPreprocessor.load_artifacts('models/')
passenger_features = preprocessor.preprocess_single_passenger({
    'pclass': 1, 'sex': 'female', 'age': 29.0,
    'sibsp': 1, 'parch': 0, 'fare': 89.10, 'embarked': 'C'
})
```

#### API Reference

**Training Methods:**
- `fit_transform(df)`: Fit preprocessor on training data and transform it
- `save_artifacts(models_dir)`: Save all preprocessing parameters to disk

**Inference Methods:**
- `load_artifacts(models_dir)`: Class method to load saved preprocessor
- `transform(df)`: Transform new data using fitted parameters
- `preprocess_single_passenger(data_dict)`: Process single passenger for API
- `get_feature_columns()`: Get ordered list of feature columns

**Data Transformations:**
- Removes unnecessary columns (name, ticket, cabin, etc.)
- Fills missing values (age→median, embarked→mode, fare→median)
- Creates family_size = sibsp + parch + 1
- Creates is_alone = (family_size == 1)
- Creates age_group categories: 0=Child, 1=Young Adult, 2=Adult, 3=Senior
- Encodes sex: male=1, female=0
- Encodes embarked: C/Q/S → numeric values

## Integration Examples

### ML API Service Integration

The ML API service can use the shared preprocessor to ensure identical data transformations:

```python
# At API startup
from shared.preprocessor import TitanicPreprocessor
preprocessor = TitanicPreprocessor.load_artifacts('models/')

# For each prediction request
@app.post("/predict")
async def predict(passenger: PassengerData):
    # Convert API request to preprocessor format
    passenger_dict = passenger.dict()
    
    # Apply same preprocessing as training
    features = preprocessor.preprocess_single_passenger(passenger_dict)
    
    # Make prediction with trained model
    prediction = model.predict_proba(features)[0, 1]
    return {"survival_probability": prediction}
```

### Training Pipeline Integration

The training pipeline uses the same preprocessor for consistency:

```python
from shared.preprocessor import TitanicPreprocessor

# Fit on training data
preprocessor = TitanicPreprocessor()
df_processed = preprocessor.fit_transform(raw_df)

# Train models
X = df_processed[preprocessor.get_feature_columns()]
y = df_processed['survived']
model.fit(X, y)

# Save both model and preprocessor
model_artifacts = {'model': model}
pickle.dump(model_artifacts, open('model.pkl', 'wb'))
preprocessor.save_artifacts('models/')
```

## File Structure

```
shared/
├── __init__.py              # Package initialization and exports
├── preprocessor.py          # Core TitanicPreprocessor class  
├── requirements.txt         # Package dependencies
├── example_usage.py         # Usage examples and demonstrations
└── README.md               # This documentation
```

## Installation

```bash
pip install -r requirements.txt
```

## Testing

Run the example usage script to verify functionality:

```bash
python shared/example_usage.py
```

This demonstrates:
- Loading saved preprocessor artifacts
- Processing single passenger data
- Making predictions with consistent preprocessing
- Feature engineering and encoding

## Dependencies

- **pandas**: Data manipulation and processing
- **numpy**: Numerical computations  
- **scikit-learn**: Label encoding and preprocessing utilities

## Consistency Guarantees

The shared preprocessor ensures:
- **Identical Transformations**: Same preprocessing in training and production
- **Feature Ordering**: Consistent column ordering for model compatibility  
- **Missing Value Handling**: Same strategies for missing data
- **Category Encoding**: Consistent label encoding with graceful handling of unseen categories
- **Feature Engineering**: Identical derived features (family_size, age_groups, etc.)

## Error Handling

The preprocessor handles common production scenarios:
- Missing required files during artifact loading
- Unseen categorical values during inference
- Invalid input data types and ranges
- Empty or malformed DataFrames

## Performance

- **Single Passenger Optimization**: Fast preprocessing for API requests
- **Batch Processing**: Efficient for larger datasets
- **Memory Efficient**: Minimal memory overhead for inference
- **Lazy Loading**: Artifacts loaded only when needed

## Next Steps

This shared preprocessing code enables:
1. **ML API Service** (`2-ml-service/`) to use identical preprocessing
2. **Frontend Integration** with consistent data validation
3. **Model Monitoring** with consistent feature engineering
4. **A/B Testing** with reproducible transformations