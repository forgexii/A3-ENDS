import pandas as pd
import numpy as np

from sklearn.preprocessing import (
    LabelEncoder,
    StandardScaler
)

from sklearn.model_selection import (
    train_test_split
)

from sklearn.feature_selection import VarianceThreshold


class FeatureEngineeringPipeline:

    def __init__(self, df: pd.DataFrame):

        self.df = df.copy()

        self.label_encoder = LabelEncoder()

        self.scaler = StandardScaler()

        self.variance_selector = VarianceThreshold(
            threshold=0.0
        )

    def clean_numeric_features(self):

        feature_columns = self.df.drop(
            columns=["Label"]
        ).columns

        for col in feature_columns:

            self.df[col] = pd.to_numeric(
                self.df[col],
                errors="coerce"
            )

        self.df.replace(
            [np.inf, -np.inf],
            np.nan,
            inplace=True
        )

        self.df.dropna(inplace=True)

    def split_features_and_labels(self):

        X = self.df.drop(columns=["Label"])

        y = self.df["Label"]

        return X, y

    def remove_low_variance_features(self, X):

        X_selected = self.variance_selector.fit_transform(X)

        return X_selected

    def encode_labels(self, y):

        y_encoded = self.label_encoder.fit_transform(y)

        return y_encoded

    def scale_features(self, X):

        X_scaled = self.scaler.fit_transform(X)

        return X_scaled

    def split_dataset(self, X, y):

        return train_test_split(
            X,
            y,
            test_size=0.2,
            random_state=42,
            stratify=y
        )

    def run_pipeline(self):

        print("Cleaning numeric features...")

        self.clean_numeric_features()

        print("Splitting features and labels...")

        X, y = self.split_features_and_labels()

        print("Removing low variance features...")

        X = self.remove_low_variance_features(X)

        print("Encoding labels...")

        y_encoded = self.encode_labels(y)

        print("Scaling features...")

        X_scaled = self.scale_features(X)

        print("Splitting dataset...")

        X_train, X_test, y_train, y_test = (
            self.split_dataset(
                X_scaled,
                y_encoded
            )
        )

        print("Feature engineering completed.")

        return (
            X_train,
            X_test,
            y_train,
            y_test
        )