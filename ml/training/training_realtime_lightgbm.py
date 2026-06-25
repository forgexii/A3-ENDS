import joblib
import numpy as np
import pandas as pd
import lightgbm as lgb

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report
)

from backend.core.paths import (
    DATASETS_DIR,
    MODELS_DIR,
    REPORTS_DIR
)


# ======================================================
# PATHS
# ======================================================

FEATURES_DIR = (
    DATASETS_DIR /
    "realtime_features/CICIDS2017"
)

MODEL_DIR = (
    MODELS_DIR /
    "lightgbm"
)

REPORT_DIR = (
    REPORTS_DIR /
    "lightgbm"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ======================================================
# LOAD DATA
# ======================================================

print("Loading arrays...")

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


# ======================================================
# TRAIN MODEL
# ======================================================

print("Training LightGBM...")

model = lgb.LGBMClassifier(

    n_estimators=100,
    learning_rate=0.1,
    max_depth=6,
    random_state=42,
    class_weight="balanced"

)

model.fit(
    X_train,
    y_train
)


# ======================================================
# PREDICTIONS
# ======================================================

print("Evaluating model...")

y_pred = model.predict(X_test)


# ======================================================
# METRICS
# ======================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision_macro = precision_score(
    y_test,
    y_pred,
    average="macro",
    zero_division=0
)

recall_macro = recall_score(
    y_test,
    y_pred,
    average="macro",
    zero_division=0
)

f1_macro = f1_score(
    y_test,
    y_pred,
    average="macro",
    zero_division=0
)

f1_weighted = f1_score(
    y_test,
    y_pred,
    average="weighted",
    zero_division=0
)


print("\n===== RESULTS =====")

print(f"Accuracy         : {accuracy:.4f}")
print(f"Macro F1 Score   : {f1_macro:.4f}  <-- HEADLINE METRIC")
print(f"Macro Precision  : {precision_macro:.4f}")
print(f"Macro Recall     : {recall_macro:.4f}")
print(f"Weighted F1      : {f1_weighted:.4f}")


# ======================================================
# CLASSIFICATION REPORT
# ======================================================

report = classification_report(
    y_test,
    y_pred
)

print("\nClassification Report:\n")

print(report)


# ======================================================
# SAVE REPORT
# ======================================================

with open(
    REPORT_DIR / "realtime_lightgbm_report.txt",
    "w"
) as f:

    f.write(report)


# ======================================================
# SAVE MODEL
# ======================================================

joblib.dump(
    model,
    MODEL_DIR /
    "lightgbm_model.pkl"
)


print("\nModel saved successfully.")