"""
Classification Engine

Classifies anomalous flows using
the trained LightGBM model.
"""

import joblib
import pandas as pd

from backend.core.paths import (
    MODELS_DIR
)


class ClassificationEngine:

    def __init__(self):

        print(
            "Loading LightGBM..."
        )

        self.model = joblib.load(
            MODELS_DIR / "lightgbm/lightgbm_model.pkl"
        )
        
        print("Loading LabelEncoder...")
        self.label_encoder = joblib.load(
            MODELS_DIR / "label_encoder.pkl"
        )

        print(
            "Classification engine ready."
        )

    # ==========================================
    # CLASSIFY
    # ==========================================

    def classify(
        self,
        features
    ):
        
        # The exact 6 features the LightGBM model was trained on
        ml_feature_names = [
            "duration",
            "packet_count",
            "mean_packet_size",
            "std_packet_size",
            "total_bytes",
            "mean_iat",
        ]

        # Strict filtering: only the 6 expected ML features, in order
        ml_only = {k: features.get(k, 0.0) for k in ml_feature_names}

        df = pd.DataFrame(
            [ml_only], columns=ml_feature_names
        )
        
        # Load the scaler (since model was trained on scaled features!)
        scaler = joblib.load(MODELS_DIR / "realtime_scaler.pkl")
        df_scaled = scaler.transform(df)

        # The model predicts the encoded integer
        pred_int = int(
            self.model.predict(
                df_scaled
            )[0]
        )
        
        # Convert back to the original string label (e.g. "PortScan", "DoS Hulk")
        prediction_str = self.label_encoder.inverse_transform([pred_int])[0]

        confidence = float(
            self.model.predict_proba(
                df_scaled
            ).max()
        )

        return {
            "classification":
                prediction_str,

            "confidence":
                confidence
        }