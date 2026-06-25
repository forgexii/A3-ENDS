import pandas as pd

from feature_engineering import FeatureEngineeringPipeline


df = pd.read_csv(
    "../../datasets/processed/CICIDS2017/cleaned_cicids2017.csv"
)

pipeline = FeatureEngineeringPipeline(df)

X_train, X_test, y_train, y_test = pipeline.run_pipeline()

print("X_train shape:", X_train.shape)
print("X_test shape:", X_test.shape)

print("y_train shape:", y_train.shape)
print("y_test shape:", y_test.shape)