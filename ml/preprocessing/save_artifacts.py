'''Artifact Saving Script for Feature Engineering Pipeline'''
import joblib
import pandas as pd

from feature_engineering import FeatureEngineeringPipeline


df = pd.read_csv(
    "../../datasets/processed/CICIDS2017/cleaned_cicids2017.csv"
)

pipeline = FeatureEngineeringPipeline(df)

X, y = pipeline.split_features_and_labels()

pipeline.encode_labels(y)

pipeline.scale_features(X)

joblib.dump(
    pipeline.label_encoder,
    "../../models/label_encoder.pkl"
)

joblib.dump(
    pipeline.scaler,
    "../../models/scaler.pkl"
)

print("Artifacts saved successfully.")