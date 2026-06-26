"""
Inference Engine

Performs realtime anomaly detection
using the trained Sparse Autoencoder.
"""

import joblib
import numpy as np
import pandas as pd

from tensorflow.keras.models import load_model

from backend.core.paths import (
    MODELS_DIR,
    DATASETS_DIR
)

from realtime.inference.classification_engine import (
    ClassificationEngine
)

from realtime.explainability.shap_engine import (
    SHAPEngine
)


class InferenceEngine:

    def __init__(self):

        self.classifier = (
            ClassificationEngine()
        )

        self.shap_engine = (
            SHAPEngine()
        )

        from realtime.risk.risk_engine import (
            RiskEngine
        )

        self.risk_engine = (
            RiskEngine()
        )

        from realtime.response.hitl_manager import (
            HITLManager
        )

        self.hitl = HITLManager()

        from realtime.response.response_manager import (
            ResponseEngine
        )

        self.response_engine = (
            ResponseEngine()
        )

        from realtime.drift.adwin_engine import (
            ADWINEngine
        )

        self.adwin = ADWINEngine()

        from realtime.rl.policy_engine import (
            PolicyEngine
        )

        self.policy_engine = (
            PolicyEngine()
        )

        print(
            "Loading autoencoder..."
        )

        self.autoencoder = load_model(

            MODELS_DIR /
            "autoencoder/sparse_autoencoder.keras"

        )

        print(
            "Loading scaler..."
        )

        self.scaler = joblib.load(
            MODELS_DIR / "realtime_scaler.pkl"
        )

        print(
            "Loading threshold..."
        )

        with open(

            MODELS_DIR /
            "autoencoder/threshold.txt",

            "r"

        ) as f:

            self.threshold = float(
                f.read().strip()
            )

        print(
            "Inference engine ready."
        )

    # ==========================================
    # FEATURE VECTOR
    # ==========================================

    def prepare_features(
        self,
        flow
    ):

        ml_features = {

            "duration":
                flow["duration"],

            "packet_count":
                flow["packet_count"],

            "mean_packet_size":
                flow["mean_packet_size"],

            "std_packet_size":
                flow["std_packet_size"],

            "total_bytes":
                flow["total_bytes"],

            "mean_iat":
                flow["mean_iat"]
        }

        return pd.DataFrame(
            [ml_features]
        )

    # ==========================================
    # SCALE
    # ==========================================

    def scale_features(
        self,
        df
    ):

        scaled = self.scaler.transform(
            df
        )

        return scaled

    # ==========================================
    # ANOMALY SCORE
    # ==========================================

    def anomaly_score(
        self,
        scaled_features
    ):

        reconstructed = (

            self.autoencoder.predict(

                scaled_features,

                verbose=0

            )

        )

        mse = np.mean(

            np.square(

                scaled_features
                -
                reconstructed

            ),

            axis=1

        )

        return float(
            mse[0]
        )

    # ==========================================
    # DETECT
    # ==========================================

    def detect(
        self,
        features
    ):

        df = self.prepare_features(
            features
        )

        scaled = self.scale_features(
            df
        )

        score = self.anomaly_score(
            scaled
        )

        result = {

            "anomaly_score":
                score,

            "threshold":
                self.threshold,

            "is_anomaly":
                score > self.threshold,

            "classification":
                None,

            "confidence":
                None,

            "explanations":
                None,

            "drift_detected":
                False,

            "drift_estimation":
                0.0
        }

        if result["is_anomaly"]:

            classification = (

                self.classifier.classify(
                    features
                )

            )

            result.update(
                classification
            )

            result["explanations"] = (

                self.shap_engine.explain(
                    features
                )

            )

            risk = self.risk_engine.evaluate(
                result
            )

            result.update(
                risk
            )
            
            # Thesis 3.2.8: ADWIN tracks risk score, not raw MSE
            drift_result = self.adwin.update(
                risk["risk_score"] / 100.0
            )
            
            result["drift_detected"] = drift_result["drift_detected"]
            result["drift_estimation"] = drift_result["estimation"]

            policy = (
                self.policy_engine.decide(
                    result
                )

            )

            result.update(
                policy
            )

            workflow = self.hitl.process(
                result
            )

            result.update(
                workflow
            )

            self.response_engine.execute(
                result
            )

        return result