"""
Titanic Dataset Preprocessor - Shared Common Code

This module contains the preprocessing logic for the Titanic dataset that can be
shared across training pipeline and ML API service components.

Key Features:
- Consistent data preprocessing across all components
- Feature engineering with family size, age groups, etc.
- Categorical encoding with saved label encoders
- Missing value handling with statistics persistence
- Production-ready preprocessing for inference

Author: Titanic ML Predictor Platform
"""

import pandas as pd
import pickle
import json
import os
from sklearn.preprocessing import LabelEncoder
from typing import Dict, List


class TitanicPreprocessor:
    """
    Handles all data preprocessing and feature engineering for the Titanic dataset.

    This class provides consistent preprocessing for both training and inference,
    ensuring that the same transformations are applied in both scenarios.
    """

    def __init__(self):
        """Initialize the preprocessor with empty state."""
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_columns: List[str] = []
        self.preprocessing_stats: Dict = {}
        self._is_fitted = False

    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fit the preprocessor on training data and transform it.

        Args:
            df (DataFrame): Training DataFrame with 'survived' column

        Returns:
            DataFrame: Preprocessed training DataFrame
        """
        print("Fitting preprocessor on training data...")
        return self._preprocess(df, is_training=True)

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform new data using fitted preprocessor parameters.

        Args:
            df (DataFrame): Input DataFrame to transform

        Returns:
            DataFrame: Preprocessed DataFrame

        Raises:
            RuntimeError: If preprocessor has not been fitted yet
        """
        if not self._is_fitted:
            raise RuntimeError(
                "Preprocessor must be fitted before transforming new data. Call fit_transform() first."
            )

        return self._preprocess(df, is_training=False)

    def _preprocess(self, df: pd.DataFrame, is_training: bool = True) -> pd.DataFrame:
        """
        Internal preprocessing method that handles both training and inference.

        Args:
            df (DataFrame): Input DataFrame
            is_training (bool): Whether this is training data

        Returns:
            DataFrame: Preprocessed DataFrame
        """
        print(f"Starting data preprocessing... (training={is_training})")
        df_processed = df.copy()

        # Record original stats if training
        if is_training:
            self.preprocessing_stats = {
                "original_shape": df.shape,
                "survival_rate": df["survived"].mean()
                if "survived" in df.columns
                else None,
            }

        # Remove unnecessary columns
        df_processed = self._remove_unnecessary_columns(df_processed)

        # Handle missing values
        self._handle_missing_values(df_processed, is_training)

        # Feature engineering
        self._create_features(df_processed)

        # Encode categorical variables
        self._encode_categorical(df_processed, is_training)

        # Set feature columns if training
        if is_training:
            self.feature_columns = [
                col for col in df_processed.columns if col != "survived"
            ]
            self._is_fitted = True

        print(f"Preprocessing complete. Final shape: {df_processed.shape}")
        return df_processed

    def _remove_unnecessary_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove columns that are not useful for prediction."""
        columns_to_remove = ["name", "ticket", "cabin", "boat", "body", "home.dest"]
        return df.drop(columns=columns_to_remove, errors="ignore")

    def _handle_missing_values(self, df: pd.DataFrame, is_training: bool) -> None:
        """
        Handle missing values in the dataset.

        Args:
            df (DataFrame): DataFrame to process (modified in-place)
            is_training (bool): Whether this is training data
        """
        print("Handling missing values...")

        # Age - fill with median
        if "age" in df.columns:
            if is_training:
                self.preprocessing_stats["age_median"] = df["age"].median()
            fill_value = self.preprocessing_stats.get("age_median", df["age"].median())
            df.loc[:, "age"] = df["age"].fillna(fill_value)

        # Embarked - fill with mode
        if "embarked" in df.columns:
            if is_training:
                self.preprocessing_stats["embarked_mode"] = df["embarked"].mode()[0]
            fill_value = self.preprocessing_stats.get(
                "embarked_mode", df["embarked"].mode()[0]
            )
            df.loc[:, "embarked"] = df["embarked"].fillna(fill_value)

        # Fare - fill with median
        if "fare" in df.columns:
            if is_training:
                self.preprocessing_stats["fare_median"] = df["fare"].median()
            fill_value = self.preprocessing_stats.get(
                "fare_median", df["fare"].median()
            )
            df.loc[:, "fare"] = df["fare"].fillna(fill_value)

    def _create_features(self, df: pd.DataFrame) -> None:
        """
        Create engineered features.

        Args:
            df (DataFrame): DataFrame to process (modified in-place)
        """
        print("Creating engineered features...")

        # Family size = siblings/spouses + parents/children + self
        if "sibsp" in df.columns and "parch" in df.columns:
            df["family_size"] = df["sibsp"] + df["parch"] + 1

        # Is alone indicator
        if "family_size" in df.columns:
            df["is_alone"] = (df["family_size"] == 1).astype(int)

        # Age groups for better pattern recognition
        if "age" in df.columns:
            df["age_group"] = pd.cut(
                df["age"],
                bins=[0, 18, 35, 60, 100],
                labels=[0, 1, 2, 3],  # Child, Young Adult, Adult, Senior
            )
            df["age_group"] = df["age_group"].astype(int)

    def _encode_categorical(self, df: pd.DataFrame, is_training: bool) -> None:
        """
        Encode categorical variables to numerical values.

        Args:
            df (DataFrame): DataFrame to process (modified in-place)
            is_training (bool): Whether this is training data
        """
        print("Encoding categorical variables...")

        categorical_columns = ["sex", "embarked"]

        for col in categorical_columns:
            if col in df.columns:
                if is_training:
                    encoder = LabelEncoder()
                    df[col] = encoder.fit_transform(df[col])
                    self.label_encoders[col] = encoder
                else:
                    if col in self.label_encoders:
                        # Handle unseen categories during inference
                        try:
                            df[col] = self.label_encoders[col].transform(df[col])
                        except ValueError:
                            print(
                                f"Warning: Unseen category in {col}. Using most frequent value."
                            )
                            # For unseen categories, use the most frequent training category
                            mode_category = self.label_encoders[col].classes_[0]
                            df[col] = df[col].map(
                                lambda x: x
                                if x in self.label_encoders[col].classes_
                                else mode_category
                            )
                            df[col] = self.label_encoders[col].transform(df[col])

    def get_feature_columns(self) -> List[str]:
        """
        Get the ordered list of feature columns.

        Returns:
            List[str]: Feature column names in correct order

        Raises:
            RuntimeError: If preprocessor has not been fitted yet
        """
        if not self._is_fitted:
            raise RuntimeError(
                "Preprocessor must be fitted before accessing feature columns."
            )
        return self.feature_columns.copy()

    def save_artifacts(self, models_dir: str) -> None:
        """
        Save preprocessor artifacts to disk.

        Args:
            models_dir (str): Directory to save artifacts

        Raises:
            RuntimeError: If preprocessor has not been fitted yet
        """
        if not self._is_fitted:
            raise RuntimeError("Preprocessor must be fitted before saving artifacts.")

        print(f"Saving preprocessor artifacts to {models_dir}/...")

        os.makedirs(models_dir, exist_ok=True)

        # Save label encoders
        with open(os.path.join(models_dir, "label_encoders.pkl"), "wb") as f:
            pickle.dump(self.label_encoders, f)

        # Save preprocessing stats
        with open(os.path.join(models_dir, "preprocessing_stats.json"), "w") as f:
            json.dump(self.preprocessing_stats, f, indent=2)

        # Save feature columns
        with open(os.path.join(models_dir, "feature_columns.json"), "w") as f:
            json.dump(self.feature_columns, f, indent=2)

    @classmethod
    def load_artifacts(cls, models_dir: str) -> "TitanicPreprocessor":
        """
        Load preprocessor artifacts from disk.

        Args:
            models_dir (str): Directory containing artifacts

        Returns:
            TitanicPreprocessor: Loaded preprocessor instance

        Raises:
            FileNotFoundError: If required artifacts are missing
        """
        print(f"Loading preprocessor artifacts from {models_dir}/...")

        preprocessor = cls()

        # Load label encoders
        encoders_path = os.path.join(models_dir, "label_encoders.pkl")
        if not os.path.exists(encoders_path):
            raise FileNotFoundError(
                f"Required file 'label_encoders.pkl' not found in {models_dir}"
            )

        with open(encoders_path, "rb") as f:
            preprocessor.label_encoders = pickle.load(f)

        # Load preprocessing stats
        stats_path = os.path.join(models_dir, "preprocessing_stats.json")
        if not os.path.exists(stats_path):
            raise FileNotFoundError(
                f"Required file 'preprocessing_stats.json' not found in {models_dir}"
            )

        with open(stats_path, "r") as f:
            preprocessor.preprocessing_stats = json.load(f)

        # Load feature columns
        features_path = os.path.join(models_dir, "feature_columns.json")
        if not os.path.exists(features_path):
            raise FileNotFoundError(
                f"Required file 'feature_columns.json' not found in {models_dir}"
            )

        with open(features_path, "r") as f:
            preprocessor.feature_columns = json.load(f)

        preprocessor._is_fitted = True

        print("✅ Preprocessor artifacts loaded successfully!")
        return preprocessor

    def preprocess_single_passenger(self, passenger_data: Dict) -> pd.DataFrame:
        """
        Preprocess a single passenger's data for inference.

        Args:
            passenger_data (Dict): Dictionary with passenger information

        Returns:
            DataFrame: Preprocessed features ready for model prediction

        Raises:
            RuntimeError: If preprocessor has not been fitted yet
        """
        if not self._is_fitted:
            raise RuntimeError(
                "Preprocessor must be fitted before preprocessing passenger data."
            )

        # Convert to DataFrame
        df = pd.DataFrame([passenger_data])

        # Apply preprocessing
        df_processed = self.transform(df)

        # Return only feature columns in correct order
        return df_processed[self.feature_columns]


def create_passenger_dataframe(
    pclass: int,
    sex: str,
    age: float,
    sibsp: int,
    parch: int,
    fare: float,
    embarked: str,
) -> pd.DataFrame:
    """
    Convenience function to create a passenger DataFrame for inference.

    Args:
        pclass (int): Passenger class (1, 2, or 3)
        sex (str): Sex ('male' or 'female')
        age (float): Age in years
        sibsp (int): Number of siblings/spouses aboard
        parch (int): Number of parents/children aboard
        fare (float): Fare paid
        embarked (str): Port of embarkation ('C', 'Q', or 'S')

    Returns:
        DataFrame: Single-row DataFrame with passenger data
    """
    passenger_data = {
        "pclass": pclass,
        "sex": sex,
        "age": age,
        "sibsp": sibsp,
        "parch": parch,
        "fare": fare,
        "embarked": embarked,
    }

    return pd.DataFrame([passenger_data])
