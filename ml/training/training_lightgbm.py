'''This code trains a LightGBM model on the CICIDS2017 dataset. 
It loads preprocessed feature arrays, initializes the model, trains it, evaluates its 
performance using various metrics, and saves the trained model for future use.'''
import joblib
import numpy as np

from lightgbm import LGBMClassifier

from sklearn.metrics import (
    classification_report,
    accuracy_score,
    confusion_matrix
)

from backend.core.paths import (
    DATASETS_DIR,
    MODELS_DIR
)


FEATURES_DIR = (
    DATASETS_DIR /
    "features/CICIDS2017"
)


print("Loading feature arrays...")

X_train = np.load(
    FEATURES_DIR / "X_train.npy"
)

X_test = np.load(
    FEATURES_DIR / "X_test.npy"
)

y_train = np.load(
    FEATURES_DIR / "y_train.npy"
)

y_test = np.load(
    FEATURES_DIR / "y_test.npy"
)


print("Initializing LightGBM model...")

model = LGBMClassifier(
    objective="multiclass",
    n_estimators=100,
    learning_rate=0.1,
    max_depth=10,
    random_state=42,
    n_jobs=4,
    verbose=-1
)


print("Training model...")

model.fit(
    X_train,
    y_train
)


print("Generating predictions...")

y_pred = model.predict(X_test)


print("Calculating metrics...")

accuracy = accuracy_score(
    y_test,
    y_pred
)

print(f"\nAccuracy: {accuracy:.4f}")


print("\nClassification Report:\n")

print(
    classification_report(
        y_test,
        y_pred
    )
)


print("\nConfusion Matrix:\n")

print(
    confusion_matrix(
        y_test,
        y_pred
    )
)


LIGHTGBM_DIR = (
    MODELS_DIR /
    "lightgbm"
)

LIGHTGBM_DIR.mkdir(
    parents=True,
    exist_ok=True
)


print("\nSaving model...")

joblib.dump(
    model,
    LIGHTGBM_DIR /
    "lightgbm_model.pkl"
)

print("Model saved successfully.")