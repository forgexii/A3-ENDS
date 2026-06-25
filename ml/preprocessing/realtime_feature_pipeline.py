import pandas as pd
import numpy as np

from sklearn.model_selection import (
    train_test_split
)

from sklearn.preprocessing import (
    LabelEncoder,
    MinMaxScaler
)

from backend.core.paths import (
    DATASETS_DIR
)


# ======================================================
# PATHS
# ======================================================

RAW_DATA_PATH = (
    DATASETS_DIR /
    "processed/CICIDS2017/cleaned_cicids2017.csv"
)

OUTPUT_DIR = (
    DATASETS_DIR /
    "realtime_features/CICIDS2017"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ======================================================
# LOAD DATA
# ======================================================

print("Loading dataset...")

df = pd.read_csv(
    RAW_DATA_PATH
)

print(df.shape)


# ======================================================
# SELECT REALTIME FEATURES
# ======================================================

print("Selecting realtime-compatible features...")


FEATURE_COLUMNS = [

    "Flow Duration",
    "Total Fwd Packets",
    "Fwd Packet Length Mean",
    "Fwd Packet Length Std",
    "Flow Bytes/s",
    "Flow IAT Mean"

]


TARGET_COLUMN = "Label"


df = df[
    FEATURE_COLUMNS +
    [TARGET_COLUMN]
]


# ======================================================
# CLEAN DATA & DROP DUPLICATES
# ======================================================

print("Cleaning data...")

df.replace(
    [np.inf, -np.inf],
    np.nan,
    inplace=True
)

df.dropna(inplace=True)

print("Dropping duplicates to prevent train/test leakage...")
initial_len = len(df)
df.drop_duplicates(subset=FEATURE_COLUMNS, inplace=True)
print(f"Dropped {initial_len - len(df)} duplicate rows. New size: {len(df)}")


# ======================================================
# LABEL MAPPING & ENCODING
# ======================================================

print("Mapping labels to 8 distinct classes...")

def map_cicids_label(x):
    x_str = str(x)
    if 'BENIGN' in x_str: return 'Benign'
    if 'DDoS' in x_str: return 'DDoS'
    if 'DoS' in x_str or 'Heartbleed' in x_str: return 'DoS'
    if 'PortScan' in x_str: return 'Portscan'
    if 'Patator' in x_str: return 'Brute Force'
    if 'Bot' in x_str: return 'Botnet'
    if 'Web Attack' in x_str: return 'Web Attack'
    if 'Infiltration' in x_str: return 'Infiltration'
    return 'Unknown'

df[TARGET_COLUMN] = df[TARGET_COLUMN].apply(map_cicids_label)

print("Encoding labels...")

encoder = LabelEncoder()

df[TARGET_COLUMN] = encoder.fit_transform(
    df[TARGET_COLUMN]
)

# Save the human-readable mapping explicitly
label_mapping = {int(i): str(label) for i, label in enumerate(encoder.classes_)}
import json
with open(OUTPUT_DIR / "label_mapping.json", "w") as f:
    json.dump(label_mapping, f, indent=4)


# ======================================================
# FEATURES / TARGET
# ======================================================

X = df[FEATURE_COLUMNS].copy()

# ==========================================
# RENAME TO REALTIME FEATURE NAMES
# ==========================================

X.columns = [

    "duration",
    "packet_count",
    "mean_packet_size",
    "std_packet_size",
    "total_bytes",
    "mean_iat"

]

y = df[TARGET_COLUMN]


# ======================================================
# NORMALIZATION
# ======================================================

print("Scaling features...")

scaler = MinMaxScaler()

X_scaled = scaler.fit_transform(X)


# ======================================================
# TRAIN TEST SPLIT
# ======================================================

print("Splitting dataset...")

X_train, X_test, y_train, y_test = (
    train_test_split(
        X_scaled,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
)


# ======================================================
# SAVE ARRAYS
# ======================================================

print("Saving arrays...")

np.save(
    OUTPUT_DIR / "X_train.npy",
    X_train
)

np.save(
    OUTPUT_DIR / "X_test.npy",
    X_test
)

np.save(
    OUTPUT_DIR / "y_train.npy",
    y_train
)

np.save(
    OUTPUT_DIR / "y_test.npy",
    y_test
)


# ======================================================
# SAVE FEATURE NAMES
# ======================================================

feature_names = [

    "duration",
    "packet_count",
    "mean_packet_size",
    "std_packet_size",
    "total_bytes",
    "mean_iat"

]

pd.Series(feature_names).to_csv(
    OUTPUT_DIR / "feature_names.csv",
    index=False
)


# ======================================================
# SAVE SCALER
# ======================================================

import joblib

joblib.dump(
    scaler,
    OUTPUT_DIR / "scaler.pkl"
)


print("\nRealtime-compatible dataset created.")
print(f"Saved to: {OUTPUT_DIR}")