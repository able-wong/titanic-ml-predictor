"""
Titanic Survival Prediction - Educational Machine Learning Script

This script demonstrates a complete machine learning pipeline:
1. Data loading and exploration
2. Data preprocessing and feature engineering
3. Training two different algorithms (Logistic Regression & Decision Tree)
4. Ensemble prediction (averaging both models)
5. Model evaluation and accuracy measurement

Author: Learning Python ML
Date: 2025-08-30
"""

# ============================================================================
# IMPORTS - All the libraries we need for our machine learning pipeline
# ============================================================================
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')  # Hide warning messages for cleaner output

# ============================================================================
# DATA LOADING AND EXPLORATION FUNCTIONS
# ============================================================================

def load_and_explore_data(train_file: str, test_file: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load the training and testing datasets and show basic information.
    
    Args:
        train_file (str): Path to training CSV file
        test_file (str): Path to testing CSV file
    
    Returns:
        tuple: (train_df, test_df) - loaded DataFrames
    """
    print("=" * 60)
    print("STEP 1: LOADING AND EXPLORING DATA")
    print("=" * 60)
    
    # TODO: Load both CSV files using pd.read_csv()
    train_df = pd.read_csv(train_file)
    test_df = pd.read_csv(test_file)
    
    print(f"Training data shape: {train_df.shape}")
    print(f"Testing data shape: {test_df.shape}")
    
    print("\nFirst few rows of training data:")
    print(train_df.head())
    
    print("\nData types and missing values:")
    print(train_df.info())
    
    print("\nSurvival statistics:")
    print("Survival rate:", train_df['survived'].mean())

    return train_df, test_df

# ============================================================================
# DATA PREPROCESSING FUNCTIONS
# ============================================================================

def preprocess_data(df, is_training=True):
    """
    Clean and preprocess the data for machine learning.
    
    This function:
    - Removes unnecessary columns
    - Handles missing values
    - Creates new features
    - Converts categorical data to numerical
    
    Args:
        df (DataFrame): Input DataFrame to preprocess
        is_training (bool): Whether this is training data (has 'survived' column)
    
    Returns:
        DataFrame: Preprocessed DataFrame ready for ML
    """

    print("\n" + "=" * 60)
    print("STEP 2: PREPROCESSING DATA")
    print("=" * 60)
    
    # Create a copy to avoid modifying original data
    df_processed = df.copy()
    
    print("Original columns:", list(df_processed.columns))
    
    # ========================================
    # Remove unnecessary columns
    # ========================================
    print("\nRemoving unnecessary columns...")
    columns_to_remove = ['name', 'ticket', 'cabin', 'boat', 'body', 'home.dest']
    # TODO: Use df_processed.drop() to remove these columns
    df_processed = df_processed.drop(columns=columns_to_remove, errors='ignore')
    
    print("Remaining columns:", list(df_processed.columns))
    
    # ========================================
    # Handle missing values
    # ========================================
    print("\nHandling missing values...")
    print("Missing values before processing:", df_processed.isnull().sum())
    
    # Fill missing ages with median age
    if 'age' in df_processed.columns:
        df_processed['age'].fillna(df_processed['age'].median(), inplace=True)

    # Fill missing embarked with mode (most common value)
    if 'embarked' in df_processed.columns:
        df_processed['embarked'].fillna(df_processed['embarked'].mode()[0], inplace=True)

    # Fill missing fare with median (if any)
    if 'fare' in df_processed.columns:
        df_processed['fare'].fillna(df_processed['fare'].median(), inplace=True)
    
    print("Missing values after processing:")
    print(df_processed.isnull().sum())
    
    # ========================================
    # Feature Engineering - Create new useful features
    # ========================================
    print("\nCreating new features...")
    
    # Create family_size feature (siblings/spouses + parents/children + 1)
    if 'sibsp' in df_processed.columns and 'parch' in df_processed.columns:
        df_processed['family_size'] = df_processed['sibsp'] + df_processed['parch'] + 1

    # Create is_alone feature (1 if traveling alone, 0 if with family)
    if 'family_size' in df_processed.columns:
        df_processed['is_alone'] = (df_processed['family_size'] == 1).astype(int)
    
    # Create age groups for better pattern recognition
    if 'age' in df_processed.columns:
        df_processed['age_group'] = pd.cut(
            df_processed['age'],
            bins=[0, 18, 35, 60, 100],
            labels=['Child', 'Young_Adult', 'Adult', 'Senior']
        )
    
    # ========================================
    # Convert categorical variables to numerical
    # ========================================
    print("\nConverting categorical variables to numerical...")
    
    # Convert sex to numerical (male=1, female=0)
    if 'sex' in df_processed.columns:
        le_sex = LabelEncoder()
        df_processed['sex'] = le_sex.fit_transform(df_processed['sex'])

    # Convert embarked to numerical
    if 'embarked' in df_processed.columns:
        le_embarked = LabelEncoder()
        df_processed['embarked'] = le_embarked.fit_transform(df_processed['embarked'])
    
    # Convert age_group to numerical if created
    if 'age_group' in df_processed.columns:
        df_processed['age_group'] = df_processed['age_group'].cat.codes

    print("\nFinal preprocessed data info:")
    print(df_processed.info())
    print("\nFirst few rows after preprocessing:")
    print(df_processed.head())
    
    return df_processed

# ============================================================================
# MODEL TRAINING FUNCTIONS
# ============================================================================

def train_logistic_regression(X_train, y_train):
    """
    Train a Logistic Regression model.
    
    Logistic Regression is good for binary classification problems.
    It finds the best line to separate survivors from non-survivors.
    
    Args:
        X_train: Training features
        y_train: Training labels (survived or not)
    
    Returns:
        Trained LogisticRegression model
    """
    print("\n" + "=" * 60)
    print("STEP 3A: TRAINING LOGISTIC REGRESSION MODEL")
    print("=" * 60)
    
    # Create the model with specific parameters for better performance
    lr_model = LogisticRegression(random_state=42, max_iter=1000)
    
    # Train the model
    lr_model.fit(X_train, y_train)
    
    print("Logistic Regression model trained successfully!")
    print(f"Model coefficients shape: {lr_model.coef_.shape}")
    
    return lr_model

def train_decision_tree(X_train, y_train):
    """
    Train a Decision Tree model.
    
    Decision Trees make decisions by asking yes/no questions about features.
    They're easy to interpret and understand.
    
    Args:
        X_train: Training features
        y_train: Training labels (survived or not)
    
    Returns:
        Trained DecisionTreeClassifier model
    """
    print("\n" + "=" * 60)
    print("STEP 3B: TRAINING DECISION TREE MODEL")
    print("=" * 60)
    
    # Create the model with parameters to prevent overfitting
    dt_model = DecisionTreeClassifier(random_state=42, max_depth=10, min_samples_split=20)
    
    # Train the model
    dt_model.fit(X_train, y_train)

    print("Decision Tree model trained successfully!")
    print(f"Tree depth: {dt_model.get_depth()}")
    print(f"Number of features used: {dt_model.n_features_in_}")
    
    return dt_model

# ============================================================================
# ENSEMBLE PREDICTION FUNCTION
# ============================================================================

def ensemble_predict(lr_model, dt_model, X_test):
    """
    Make predictions using both models and average the results.
    
    Ensemble methods often perform better than individual models
    because they combine different perspectives.
    
    Args:
        lr_model: Trained Logistic Regression model
        dt_model: Trained Decision Tree model
        X_test: Test features to predict
    
    Returns:
        numpy array: Final predictions (0 or 1)
    """
    print("\n" + "=" * 60)
    print("STEP 4: ENSEMBLE PREDICTION")
    print("=" * 60)
    
    # Get probability predictions from both models
    # TODO: Use lr_model.predict_proba()[:,1] to get survival probabilities
    lr_probs = lr_model.predict_proba(X_test)[:,1]
    # TODO: Get probabilities from decision tree model
    dt_probs = dt_model.predict_proba(X_test)[:,1]

    # Average the probabilities
    ensemble_probs = (lr_probs + dt_probs) / 2

    # Convert probabilities to binary predictions (threshold = 0.5)
    ensemble_predictions = (ensemble_probs >= 0.5).astype(int)
    
    print(f"Logistic Regression average probability: {lr_probs.mean():.3f}")
    print(f"Decision Tree average probability: {dt_probs.mean():.3f}")
    print(f"Ensemble average probability: {ensemble_probs.mean():.3f}")
    
    return ensemble_predictions

# ============================================================================
# MODEL EVALUATION FUNCTION
# ============================================================================

def evaluate_model(y_true, y_pred, model_name="Model"):
    """
    Evaluate model performance using multiple metrics.
    
    Args:
        y_true: Actual labels
        y_pred: Predicted labels
        model_name: Name of the model for display
    """
    print(f"\n{model_name} Evaluation:")
    print("-" * 40)
    
    # Calculate accuracy
    accuracy = accuracy_score(y_true, y_pred)
    print(f"Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
    
    # Show confusion matrix
    cm = confusion_matrix(y_true, y_pred)

    print("\nConfusion Matrix:")
    print("    Predicted")
    print("      0    1")
    print(f"Actual 0  {cm[0,0]:3d}  {cm[0,1]:3d}")
    print(f"       1  {cm[1,0]:3d}  {cm[1,1]:3d}")
    
    # Show detailed classification report
    print(f"\nDetailed Classification Report for {model_name}:")
    report = classification_report(y_true, y_pred, output_dict=True)
    for label, metrics in report.items():
        if label == "accuracy":
            continue
        print(f"Class {label}:")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.3f}")

    return accuracy

# ============================================================================
# MAIN FUNCTION - ORCHESTRATES THE ENTIRE PIPELINE
# ============================================================================

def main():
    """
    Main function that runs the complete machine learning pipeline.
    """
    print("🚢 TITANIC SURVIVAL PREDICTION - MACHINE LEARNING PIPELINE 🚢")
    print("This script will predict passenger survival using ML algorithms")
    
    try:
        # Step 1: Load original dataset
        print("=" * 60)
        print("STEP 1: LOADING ORIGINAL DATASET")
        print("=" * 60)
        
        # Load the original dataset
        original_df = pd.read_csv('data/titanic passenger list.csv')
        print(f"Original dataset shape: {original_df.shape}")
        print(f"Columns: {list(original_df.columns)}")
        print(f"Survival rate: {original_df['survived'].mean():.3f}")
        
        print("\nFirst few rows:")
        print(original_df.head())
        
        # Step 2: Preprocess the entire dataset
        processed_df = preprocess_data(original_df, is_training=True)
        
        # Step 3: Split preprocessed data into train/test (80/20)
        print("\n" + "=" * 60)
        print("STEP 3: SPLITTING INTO TRAIN/TEST SETS")
        print("=" * 60)
        
        # Prepare features and labels
        feature_columns = [col for col in processed_df.columns if col != 'survived']
        X = processed_df[feature_columns]
        y = processed_df['survived']
        
        print(f"Features used: {feature_columns}")
        print(f"Total samples: {len(X)}")
        
        # Split with stratification to maintain survival rate in both sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {X_train.shape[0]} samples")
        print(f"Test set: {X_test.shape[0]} samples")
        print(f"Training survival rate: {y_train.mean():.3f}")
        print(f"Test survival rate: {y_test.mean():.3f}")
        
        # Step 4: Train models
        lr_model = train_logistic_regression(X_train, y_train)
        dt_model = train_decision_tree(X_train, y_train)
        
        # Step 5: Make ensemble predictions
        ensemble_pred = ensemble_predict(lr_model, dt_model, X_test)
        
        # Step 6: Evaluate models
        print("\n" + "=" * 60)
        print("STEP 6: MODEL EVALUATION")
        print("=" * 60)
        
        # Evaluate individual models
        lr_pred = lr_model.predict(X_test)
        dt_pred = dt_model.predict(X_test)
        
        lr_accuracy = evaluate_model(y_test, lr_pred, "Logistic Regression")
        dt_accuracy = evaluate_model(y_test, dt_pred, "Decision Tree")
        ensemble_accuracy = evaluate_model(y_test, ensemble_pred, "Ensemble Model")
        
        # Final summary
        print("\n" + "=" * 60)
        print("FINAL RESULTS SUMMARY")
        print("=" * 60)
        print(f"Logistic Regression Accuracy: {lr_accuracy:.3f} ({lr_accuracy*100:.1f}%)")
        print(f"Decision Tree Accuracy:       {dt_accuracy:.3f} ({dt_accuracy*100:.1f}%)")
        print(f"Ensemble Model Accuracy:      {ensemble_accuracy:.3f} ({ensemble_accuracy*100:.1f}%)")
        
        best_accuracy = max(lr_accuracy, dt_accuracy, ensemble_accuracy)
        if best_accuracy == ensemble_accuracy:
            print("\n🏆 The Ensemble Model performed the best!")
        elif best_accuracy == lr_accuracy:
            print("\n🏆 Logistic Regression performed the best!")
        else:
            print("\n🏆 Decision Tree performed the best!")
            
        print(f"\nBest accuracy achieved: {best_accuracy:.3f} ({best_accuracy*100:.1f}%)")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        print("Please check that 'data/titanic passenger list.csv' exists in the current directory.")

# ============================================================================
# RUN THE PROGRAM
# ============================================================================

if __name__ == "__main__":
    main()

# ============================================================================
# LEARNING NOTES FOR COMPLETION:
# ============================================================================
"""
TODO: Complete the following functions by filling in the missing lines:

1. load_and_explore_data():
   - Load test_df using pd.read_csv()
   - Calculate survival rate using mean()

2. preprocess_data():
   - Drop unnecessary columns
   - Fill missing values with median/mode
   - Create family_size, is_alone, age_group features
   - Convert categorical variables to numerical

3. train_logistic_regression():
   - Create LogisticRegression model
   - Fit the model with training data

4. train_decision_tree():
   - Create DecisionTreeClassifier
   - Train the model

5. ensemble_predict():
   - Get predictions from both models
   - Average the probabilities
   - Convert to binary predictions

6. evaluate_model():
   - Calculate accuracy score
   - Create confusion matrix
   - Generate classification report

Key ML Concepts Demonstrated:
- Data preprocessing and feature engineering
- Handling missing values
- Training multiple algorithms
- Ensemble methods (averaging predictions)
- Model evaluation with multiple metrics
- Cross-validation concepts

Python Libraries Used:
- pandas: Data manipulation and analysis
- numpy: Numerical computations
- scikit-learn: Machine learning algorithms and metrics
"""