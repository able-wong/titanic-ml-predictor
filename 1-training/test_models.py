"""
Titanic Survival Prediction - Model Testing CLI

Interactive CLI tool to test trained models with passenger information.
This script loads the trained models and allows manual testing of predictions.

Features:
- Interactive passenger data input
- Survival probability predictions
- Individual model contributions
- Ensemble prediction results

Author: Titanic ML Predictor Platform
"""

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import pickle
from shared.preprocessor import TitanicPreprocessor

MODELS_DIR = "../models"


class ModelTester:
    """Handles loading and testing of trained models."""

    def __init__(self):
        self.lr_model = None
        self.dt_model = None
        self.preprocessor = None

    def load_models(self):
        """Load all trained models and preprocessing components."""
        print("Loading trained models and preprocessing components...")

        # Check if models directory exists
        if not os.path.exists(MODELS_DIR):
            raise FileNotFoundError(
                f"Models directory '{MODELS_DIR}' not found. Run train.py first."
            )

        # Load models
        model_files = ["logistic_model.pkl", "decision_tree_model.pkl"]

        for filename in model_files:
            filepath = os.path.join(MODELS_DIR, filename)
            if not os.path.exists(filepath):
                raise FileNotFoundError(
                    f"Required file '{filename}' not found in models directory."
                )

        # Load logistic regression model
        with open(os.path.join(MODELS_DIR, "logistic_model.pkl"), "rb") as f:
            self.lr_model = pickle.load(f)

        # Load decision tree model
        with open(os.path.join(MODELS_DIR, "decision_tree_model.pkl"), "rb") as f:
            self.dt_model = pickle.load(f)

        # Load preprocessor
        self.preprocessor = TitanicPreprocessor.load_artifacts(MODELS_DIR)

        print("✅ All models and preprocessing components loaded successfully!")

    def get_passenger_info(self):
        """Get passenger information from user input."""
        print("\n" + "=" * 60)
        print("ENTER PASSENGER INFORMATION")
        print("=" * 60)

        passenger_data = {}

        # Basic information
        try:
            passenger_data["pclass"] = int(
                input("Passenger Class (1=First, 2=Second, 3=Third): ")
            )
            if passenger_data["pclass"] not in [1, 2, 3]:
                raise ValueError("Class must be 1, 2, or 3")

            sex_input = input("Sex (male/female): ").lower().strip()
            if sex_input not in ["male", "female"]:
                raise ValueError("Sex must be 'male' or 'female'")
            passenger_data["sex"] = sex_input

            passenger_data["age"] = float(input("Age (years): "))
            if passenger_data["age"] < 0 or passenger_data["age"] > 120:
                raise ValueError("Age must be between 0 and 120")

            passenger_data["sibsp"] = int(input("Siblings/Spouses aboard: "))
            passenger_data["parch"] = int(input("Parents/Children aboard: "))

            passenger_data["fare"] = float(input("Fare paid: "))

            embarked_input = (
                input("Embarked (C=Cherbourg, Q=Queenstown, S=Southampton): ")
                .upper()
                .strip()
            )
            if embarked_input not in ["C", "Q", "S"]:
                raise ValueError("Embarked must be C, Q, or S")
            passenger_data["embarked"] = embarked_input

        except (ValueError, KeyboardInterrupt) as e:
            if isinstance(e, KeyboardInterrupt):
                print("\n\nOperation cancelled by user.")
                return None
            print(f"Invalid input: {e}")
            return None

        return passenger_data

    def preprocess_passenger(self, passenger_data):
        """Preprocess passenger data for prediction."""
        return self.preprocessor.preprocess_single_passenger(passenger_data)

    def predict(self, passenger_data):
        """Make predictions for a passenger."""
        print("\n" + "=" * 60)
        print("PREDICTION RESULTS")
        print("=" * 60)

        try:
            # Preprocess the data
            X = self.preprocess_passenger(passenger_data)

            # Get predictions from both models
            lr_proba = self.lr_model.predict_proba(X)[0, 1]
            dt_proba = self.dt_model.predict_proba(X)[0, 1]

            # Ensemble prediction
            ensemble_proba = (lr_proba + dt_proba) / 2
            ensemble_pred = int(ensemble_proba >= 0.5)

            # Display individual model results
            print("Logistic Regression:")
            print(f"  Survival Probability: {lr_proba:.3f} ({lr_proba * 100:.1f}%)")
            print(
                f"  Prediction: {'SURVIVED' if lr_proba >= 0.5 else 'DID NOT SURVIVE'}"
            )

            print("\nDecision Tree:")
            print(f"  Survival Probability: {dt_proba:.3f} ({dt_proba * 100:.1f}%)")
            print(
                f"  Prediction: {'SURVIVED' if dt_proba >= 0.5 else 'DID NOT SURVIVE'}"
            )

            print("\n🎯 ENSEMBLE PREDICTION:")
            print(
                f"  Survival Probability: {ensemble_proba:.3f} ({ensemble_proba * 100:.1f}%)"
            )
            print(
                f"  Final Prediction: {'✅ SURVIVED' if ensemble_pred else '❌ DID NOT SURVIVE'}"
            )

            # Confidence level
            confidence = abs(ensemble_proba - 0.5) * 2
            if confidence > 0.7:
                confidence_level = "High"
            elif confidence > 0.4:
                confidence_level = "Medium"
            else:
                confidence_level = "Low"

            print(f"  Confidence Level: {confidence_level} ({confidence:.3f})")

        except Exception as e:
            print(f"❌ Error making prediction: {str(e)}")
            return None

    def display_passenger_summary(self, passenger_data):
        """Display a summary of the passenger information."""
        print("\n" + "-" * 60)
        print("PASSENGER SUMMARY")
        print("-" * 60)
        print(
            f"Class: {passenger_data['pclass']} ({'First' if passenger_data['pclass'] == 1 else 'Second' if passenger_data['pclass'] == 2 else 'Third'})"
        )
        print(f"Sex: {passenger_data['sex'].title()}")
        print(f"Age: {passenger_data['age']}")
        print(
            f"Family: {passenger_data['sibsp']} siblings/spouses, {passenger_data['parch']} parents/children"
        )
        print(f"Fare: ${passenger_data['fare']:.2f}")
        embarked_full = {"C": "Cherbourg", "Q": "Queenstown", "S": "Southampton"}
        print(f"Embarked: {embarked_full[passenger_data['embarked']]}")


def main():
    """Main interactive testing loop."""
    print("🚢 TITANIC SURVIVAL PREDICTION - MODEL TESTING CLI 🚢")
    print("=" * 80)
    print("This tool loads trained models and allows you to test survival predictions")
    print("for individual passengers.")

    try:
        # Initialize and load models
        tester = ModelTester()
        tester.load_models()

        print(
            f"\nModels ready! Using features: {tester.preprocessor.get_feature_columns()}"
        )

        while True:
            print("\n" + "=" * 80)
            print("OPTIONS:")
            print("1. Test passenger survival prediction")
            print("2. Exit")

            try:
                choice = input("\nEnter your choice (1-2): ").strip()

                if choice == "1":
                    # Get passenger information
                    passenger_data = tester.get_passenger_info()
                    if passenger_data is None:
                        continue

                    # Display summary
                    tester.display_passenger_summary(passenger_data)

                    # Make prediction
                    tester.predict(passenger_data)

                elif choice == "2":
                    print("\n👋 Thank you for using the Titanic Survival Predictor!")
                    break

                else:
                    print("Invalid choice. Please enter 1 or 2.")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Make sure you have run 'python train.py' first to train the models.")


if __name__ == "__main__":
    main()
