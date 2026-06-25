"""
SHAP Explainability Engine

Generates per-feature contribution scores for LightGBM predictions.
Only the 6 ML features used by the model are accepted; any extra metadata
fields (source_ip, destination_ip, etc.) are stripped before calling the
SHAP explainer to avoid column-mismatch errors.
"""

import joblib
import shap
import pandas as pd

from backend.core.paths import MODELS_DIR

# The exact 6 features the LightGBM model was trained on
ML_FEATURE_NAMES = [
    "duration",
    "packet_count",
    "mean_packet_size",
    "std_packet_size",
    "total_bytes",
    "mean_iat",
]


class SHAPEngine:

    def __init__(self):
        print("Loading SHAP explainer...")
        self.model = joblib.load(
            MODELS_DIR / "lightgbm/lightgbm_model.pkl"
        )
        self.explainer = shap.TreeExplainer(self.model)
        print("SHAP engine ready.")

    # ==========================================
    # EXPLAIN
    # ==========================================

    def explain(self, features: dict) -> dict:
        """
        Compute SHAP feature contributions.

        Args:
            features: dict that may contain any keys — only the 6 ML
                      features are passed to the explainer.

        Returns:
            dict mapping each of the 6 feature names to its SHAP value (float).
        """
        # Strict filtering: only the 6 expected ML features, in order
        ml_only = {k: features.get(k, 0.0) for k in ML_FEATURE_NAMES}
        df = pd.DataFrame([ml_only], columns=ML_FEATURE_NAMES)

        shap_values = self.explainer.shap_values(df)

        # Multi-class returns a list; take the class with the highest prediction
        if isinstance(shap_values, list):
            # Pick the class dimension for the predicted class (argmax of first row)
            import numpy as np
            proba = self.model.predict_proba(df)[0]
            pred_class = int(np.argmax(proba))
            values = shap_values[pred_class][0]
        else:
            values = shap_values[0]

        return {
            feature: float(values[i])
            for i, feature in enumerate(ML_FEATURE_NAMES)
        }