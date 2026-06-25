'''Feature Building Script for CICIDS2017 Dataset'''
import joblib
import numpy as np
import pandas as pd

from sklearn.preprocessing import (
    StandardScaler,
    LabelEncoder
)

from sklearn.model_selection import (
    train_test_split
)

from sklearn.feature_selection import (
    VarianceThreshold
)

from backend.core.paths import (
    DATASETS_DIR,
    MODELS_DIR
)


print("Loading cleaned dataset...")

df = pd.read_csv(
    DATASETS_DIR /
    "processed/CICIDS2017/cleaned_cicids2017.csv"
)

print("Separating features and labels...")

X = df.drop(columns=["Label"])

y = df["Label"]


print("Converting features to numeric...")

X = X.apply(
    pd.to_numeric,
    errors="coerce"
)

print("Replacing infinities...")

X.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)

print("Dropping invalid rows...")

valid_indices = X.dropna().index

X = X.loc[valid_indices]

y = y.loc[valid_indices]


print("Removing low variance features...")

selector = VarianceThreshold(
    threshold=0.0
)

X_selected = selector.fit_transform(X)

selected_feature_names = X.columns[
    selector.get_support()
]

X = X_selected


print("Encoding labels...")

label_encoder = LabelEncoder()

y_encoded = label_encoder.fit_transform(y)


print("Scaling features...")

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


print("Splitting dataset...")

X_train, X_test, y_train, y_test = (
    train_test_split(
        X_scaled,
        y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded
    )
)


FEATURES_DIR = (
    DATASETS_DIR /
    "features/CICIDS2017"
)

print("Saving NumPy arrays...")

np.save(
    FEATURES_DIR / "X_train.npy",
    X_train
)

np.save(
    FEATURES_DIR / "X_test.npy",
    X_test
)

np.save(
    FEATURES_DIR / "y_train.npy",
    y_train
)

np.save(
    FEATURES_DIR / "y_test.npy",
    y_test
)


print("Saving preprocessing artifacts...")

joblib.dump(
    scaler,
    MODELS_DIR / "scaler.pkl"
)

joblib.dump(
    label_encoder,
    MODELS_DIR / "label_encoder.pkl"
)

joblib.dump(
    selector,
    MODELS_DIR / "variance_selector.pkl"
)

joblib.dump(
    selected_feature_names.tolist(),
    MODELS_DIR / "selected_features.pkl"
)

print("Feature building completed successfully.")