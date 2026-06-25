import joblib
import shap
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

MODEL_PATH = (
    MODELS_DIR /
    "lightgbm/lightgbm_model.pkl"
)

REPORT_DIR = (
    REPORTS_DIR /
    "shap"
)

REPORT_DIR.mkdir(
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


print("Loading feature names...")

feature_names_df = pd.read_csv(
    FEATURES_DIR /
    "feature_names.csv",
    header=0
)
feature_names = feature_names_df["0"].tolist()


# ======================================================
# CREATE DATAFRAME
# ======================================================

sample_size = 1000

X_sample = X_test[:sample_size]

sample_df = pd.DataFrame(
    X_sample,
    columns=feature_names
)


# ======================================================
# LOAD MODEL
# ======================================================

print("Loading trained LightGBM model...")

model = joblib.load(
    MODEL_PATH
)


# ======================================================
# CREATE SHAP EXPLAINER
# ======================================================

print("Initializing SHAP explainer...")

explainer = shap.TreeExplainer(
    model
)


# ======================================================
# COMPUTE SHAP VALUES
# ======================================================

print("Computing SHAP values...")

shap_values = explainer.shap_values(
    sample_df
)


# ======================================================
# HANDLE MULTICLASS OUTPUT
# ======================================================

# For multiclass LightGBM,
# shap_values becomes a list.

class_index = 0

if isinstance(shap_values, list):

    print("Multiclass SHAP detected.")

    shap_matrix = shap_values[class_index]

else:

    shap_matrix = shap_values


# Reduce 3D to 2D if needed
if len(shap_matrix.shape) == 3:

    print("3D SHAP matrix detected. Reducing to 2D...")

    shap_matrix = np.mean(
        shap_matrix,
        axis=2
    )


# ======================================================
# SUMMARY PLOT
# ======================================================

print("Generating SHAP summary plot...")

plt.figure(figsize=(12, 8))

shap.summary_plot(
    shap_matrix,
    sample_df,
    feature_names=feature_names,
    show=False
)

plt.tight_layout()

plt.savefig(
    REPORT_DIR /
    "shap_summary.png",
    bbox_inches="tight",
    dpi=120
)

plt.close()


# ======================================================
# FEATURE IMPORTANCE BAR PLOT
# ======================================================

print("Generating SHAP feature importance plot...")


# Handle possible 3D SHAP output (already reduced above)
shap_matrix_reduced = np.abs(
    shap_matrix
)


# Mean importance across samples
mean_abs_shap = np.mean(
    shap_matrix_reduced,
    axis=0
)


# Ensure 1D vector
mean_abs_shap = np.ravel(
    mean_abs_shap
)


importance_df = pd.DataFrame({
    "Feature": feature_names,
    "Importance": mean_abs_shap
})

importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)


importance_df.to_csv(
    REPORT_DIR /
    "shap_feature_importance.csv",
    index=False
)


top_features = importance_df.head(20)


plt.figure(figsize=(12, 8))

plt.barh(
    top_features["Feature"],
    top_features["Importance"]
)

plt.gca().invert_yaxis()

plt.xlabel("Mean Absolute SHAP Value")

plt.title(
    "Top 20 SHAP Important Features"
)

plt.tight_layout()

plt.savefig(
    REPORT_DIR /
    "shap_bar.png",
    bbox_inches="tight",
    dpi=120
)

plt.close()


# ======================================================
# LOCAL EXPLANATION
# ======================================================

print("Generating local explanation...")

sample_index = 0

local_values = shap_matrix[sample_index]

if len(local_values.shape) == 2:

    local_values = np.mean(
        local_values,
        axis=1
    )

explanation = shap.Explanation(
    values=local_values,
    base_values=explainer.expected_value[class_index],
    data=sample_df.iloc[sample_index],
    feature_names=feature_names
)


plt.figure(figsize=(12, 8))

shap.plots.waterfall(
    explanation,
    show=False
)

plt.tight_layout()

plt.savefig(
    REPORT_DIR /
    "local_waterfall_plot.png",
    bbox_inches="tight",
    dpi=120
)

plt.close()


# ======================================================
# DEPENDENCE PLOT
# ======================================================

print("Generating dependence plot...")

top_feature = (
    importance_df.iloc[0]["Feature"]
)

shap.dependence_plot(
    top_feature,
    shap_matrix,
    sample_df,
    show=False
)

plt.tight_layout()

plt.savefig(
    REPORT_DIR /
    "dependence_plot.png",
    bbox_inches="tight",
    dpi=120
)

plt.close()


# ======================================================
# COMPLETE
# ======================================================

print("\nSHAP analysis completed successfully.")
print(f"Reports saved to: {REPORT_DIR}")