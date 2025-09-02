"""
Example usage of the shared TitanicPreprocessor for ML API integration.

This demonstrates how the ML API service can use the shared preprocessing code
to ensure consistent data transformations between training and inference.
"""

import os
import sys
import pickle

# Add the parent directory to sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from shared.preprocessor import TitanicPreprocessor, create_passenger_dataframe


def example_api_prediction():
    """
    Example of how the ML API service would use the shared preprocessor
    for making predictions on new passenger data.
    """
    print("🚢 Example: ML API using shared preprocessing 🚢")
    print("=" * 60)

    # 1. Load the preprocessor (this would be done once at API startup)
    models_dir = "models"

    if not os.path.exists(models_dir):
        print("❌ Models directory not found. Run the training pipeline first.")
        return

    try:
        # Load preprocessor with all fitted parameters
        preprocessor = TitanicPreprocessor.load_artifacts(models_dir)

        # Load trained models (example with logistic regression)
        with open(os.path.join(models_dir, "logistic_model.pkl"), "rb") as f:
            model = pickle.load(f)

        print("✅ Preprocessor and model loaded successfully!")

        # 2. Example passenger data (this would come from API request)
        passenger_data = {
            "pclass": 1,
            "sex": "female",
            "age": 29.0,
            "sibsp": 1,
            "parch": 0,
            "fare": 89.1042,
            "embarked": "C",
        }

        print(f"\n📋 Input passenger data: {passenger_data}")

        # 3. Preprocess the data using shared preprocessor
        X_processed = preprocessor.preprocess_single_passenger(passenger_data)

        print(f"🔧 Processed features shape: {X_processed.shape}")
        print(f"🔧 Feature columns: {preprocessor.get_feature_columns()}")
        print(f"🔧 Processed values: {X_processed.iloc[0].tolist()}")

        # 4. Make prediction
        survival_prob = model.predict_proba(X_processed)[0, 1]
        prediction = int(survival_prob >= 0.5)

        print("\n🎯 Prediction Results:")
        print(
            f"   Survival probability: {survival_prob:.3f} ({survival_prob * 100:.1f}%)"
        )
        print(f"   Prediction: {'SURVIVED' if prediction else 'DID NOT SURVIVE'}")

        # 5. Demonstrate convenience function
        print("\n📝 Alternative using convenience function:")
        passenger_df = create_passenger_dataframe(
            pclass=3, sex="male", age=22.0, sibsp=1, parch=0, fare=7.25, embarked="S"
        )

        X_processed_alt = preprocessor.transform(passenger_df)
        X_features_alt = X_processed_alt[preprocessor.get_feature_columns()]

        survival_prob_alt = model.predict_proba(X_features_alt)[0, 1]
        prediction_alt = int(survival_prob_alt >= 0.5)

        print("   Input: 3rd class male, age 22, fare $7.25")
        print(
            f"   Survival probability: {survival_prob_alt:.3f} ({survival_prob_alt * 100:.1f}%)"
        )
        print(f"   Prediction: {'SURVIVED' if prediction_alt else 'DID NOT SURVIVE'}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")


def show_preprocessor_features():
    """Show the available features and preprocessing capabilities."""
    print("\n🔍 TitanicPreprocessor Features:")
    print("=" * 60)
    print("✅ Consistent preprocessing between training and inference")
    print("✅ Automatic missing value handling")
    print("✅ Feature engineering (family_size, is_alone, age_groups)")
    print("✅ Categorical encoding with saved label encoders")
    print("✅ Proper feature ordering for model compatibility")
    print("✅ Single passenger and batch processing support")
    print("✅ Artifact persistence and loading")
    print("✅ Error handling for unseen categories")


if __name__ == "__main__":
    show_preprocessor_features()
    example_api_prediction()
