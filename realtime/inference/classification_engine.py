"""
Classification Engine

Classifies anomalous flows using
the trained XGBoost model.
"""

import joblib
import pandas as pd

from backend.core.paths import (
    MODELS_DIR
)


class ClassificationEngine:

    def __init__(self):

        print(
            "Loading XGBoost..."
        )

        self.model = joblib.load(
            MODELS_DIR / "xgboost/xgboost_model.pkl"
        )
        
        import json
        mapping_file = MODELS_DIR / "label_mapping.json"
        if not mapping_file.exists():
            mapping_file = MODELS_DIR.parent / "datasets/realtime_features/CICIDS2017/label_mapping.json"
        if mapping_file.exists():
            with open(mapping_file, "r") as f:
                raw_map = json.load(f)
                self.label_map = {int(k): v for k, v in raw_map.items()}
        else:
            self.label_map = {
                0: "Benign", 1: "Botnet", 2: "Brute Force", 3: "DDoS",
                4: "DoS", 5: "Infiltration", 6: "Portscan", 7: "Web Attack"
            }

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
        
        # Convert back to human-readable canonical class label
        prediction_str = self.label_map.get(pred_int, f"Class_{pred_int}")

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