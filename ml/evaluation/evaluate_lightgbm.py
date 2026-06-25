# LightGBM Evaluation Export Script
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
    precision_score,
    recall_score,
    f1_score
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

LIGHTGBM_MODEL_PATH = (
    MODELS_DIR /
    "lightgbm/lightgbm_model.pkl"
)

EVALUATION_DIR = (
    REPORTS_DIR /
    "lightgbm"
)

EVALUATION_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ======================================================
# LOAD DATA
# ======================================================

print("Loading test arrays...")

X_test = np.load(
    FEATURES_DIR / "X_test.npy"
)

y_test = np.load(
    FEATURES_DIR / "y_test.npy"
)


print("Loading trained model...")

model = joblib.load(
    LIGHTGBM_MODEL_PATH
)


# ======================================================
# PREDICTIONS
# ======================================================

print("Generating predictions...")

y_pred = model.predict(X_test)


# ======================================================
# METRICS
# ======================================================

print("Calculating evaluation metrics...")

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    average="weighted"
)

recall = recall_score(
    y_test,
    y_pred,
    average="weighted"
)

f1 = f1_score(
    y_test,
    y_pred,
    average="weighted"
)


metrics_df = pd.DataFrame([
    {
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1-Score": f1
    }
])


print(metrics_df)


metrics_df.to_csv(
    EVALUATION_DIR / "overall_metrics.csv",
    index=False
)


# ======================================================
# CLASSIFICATION REPORT
# ======================================================

print("Generating classification report...")

report = classification_report(
    y_test,
    y_pred,
    output_dict=True
)

report_df = pd.DataFrame(report).transpose()

report_df.to_csv(
    EVALUATION_DIR /
    "classification_report.csv"
)


# ======================================================
# CONFUSION MATRIX
# ======================================================

print("Generating confusion matrix...")

cm = confusion_matrix(
    y_test,
    y_pred,
    normalize='true'
)

fig, ax = plt.subplots(
    figsize=(12, 10),
    dpi=100
)


disp = ConfusionMatrixDisplay(
    confusion_matrix=cm
)


disp.plot(
    cmap="Blues",
    xticks_rotation=45,
    ax=ax,
    values_format='.2f'
)


plt.title(
    "Normalized LightGBM Confusion Matrix",
    fontsize=18,
    pad=20
)

plt.xlabel(
    "Predicted Label",
    fontsize=12
)

plt.ylabel(
    "True Label",
    fontsize=12
)

plt.tight_layout()


plt.savefig(
    EVALUATION_DIR /
    "confusion_matrix.png",
    bbox_inches="tight"
)

plt.close()


# ======================================================
# FEATURE IMPORTANCE
# ======================================================

print("Generating feature importance report...")

feature_names_df = pd.read_csv(
    FEATURES_DIR /
    "feature_names.csv",
    header=0
)
feature_names = feature_names_df["0"].tolist()


feature_importance = pd.DataFrame({
    "Feature": feature_names,
    "Importance": model.feature_importances_
})


feature_importance = feature_importance.sort_values(
    by="Importance",
    ascending=False
)


feature_importance.to_csv(
    EVALUATION_DIR /
    "feature_importance.csv",
    index=False
)


# ======================================================
# FEATURE IMPORTANCE PLOT
# ======================================================

print("Generating feature importance plot...")


top_features = feature_importance.head(20)


plt.figure(
    figsize=(12, 8),
    dpi=100
)


plt.barh(
    top_features["Feature"],
    top_features["Importance"]
)


plt.gca().invert_yaxis()


plt.title(
    "Top 20 Most Important Features",
    fontsize=18
)


plt.xlabel(
    "Importance Score",
    fontsize=12
)


plt.tight_layout()


plt.savefig(
    EVALUATION_DIR /
    "feature_importance.png",
    bbox_inches="tight"
)

plt.close()


# ======================================================
# CLASS DISTRIBUTION
# ======================================================

print("Saving class distribution...")

unique, counts = np.unique(
    y_test,
    return_counts=True
)


distribution_df = pd.DataFrame({
    "Class": unique,
    "Count": counts
})


distribution_df.to_csv(
    EVALUATION_DIR /
    "class_distribution.csv",
    index=False
)


# ======================================================
# COMPLETED
# ======================================================

print("\nEvaluation completed successfully.")
print(f"Reports saved to: {EVALUATION_DIR}")
