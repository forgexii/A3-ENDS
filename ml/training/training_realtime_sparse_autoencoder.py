import numpy as np
import matplotlib.pyplot as plt

from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input,
    Dense
)

from tensorflow.keras.regularizers import l1

from tensorflow.keras.callbacks import (
    EarlyStopping
)

from sklearn.metrics import (
    mean_squared_error
)

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

MODEL_DIR = (
    MODELS_DIR /
    "autoencoder"
)

REPORT_DIR = (
    REPORTS_DIR /
    "autoencoder"
)

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ======================================================
# LOAD DATA
# ======================================================

print("Loading arrays...")

X_train = np.load(
    FEATURES_DIR / "X_train.npy"
)

X_test = np.load(
    FEATURES_DIR / "X_test.npy"
)

y_train = np.load(
    FEATURES_DIR / "y_train.npy"
)

y_test = np.load(
    FEATURES_DIR / "y_test.npy"
)


# ======================================================
# NORMAL TRAFFIC ONLY
# ======================================================

print("Extracting benign traffic...")

X_train_normal = X_train[
    y_train == 0
]

X_test_normal = X_test[
    y_test == 0
]


print(
    f"Normal train samples: "
    f"{len(X_train_normal)}"
)


# ======================================================
# AUTOENCODER ARCHITECTURE
# ======================================================

input_dim = X_train.shape[1]

print(f"Input dimension: {input_dim}")


input_layer = Input(
    shape=(input_dim,)
)


# Encoder
encoded = Dense(
    16,
    activation="relu",
    activity_regularizer=l1(1e-5)
)(input_layer)

encoded = Dense(
    8,
    activation="relu"
)(encoded)

encoded = Dense(
    4,
    activation="relu"
)(encoded)


# Decoder
decoded = Dense(
    8,
    activation="relu"
)(encoded)

decoded = Dense(
    16,
    activation="relu"
)(decoded)

decoded = Dense(
    input_dim,
    activation="sigmoid"
)(decoded)


# Build model
autoencoder = Model(
    input_layer,
    decoded
)


# ======================================================
# COMPILE
# ======================================================

autoencoder.compile(
    optimizer="adam",
    loss="mse"
)


autoencoder.summary()


# ======================================================
# CALLBACKS
# ======================================================

early_stop = EarlyStopping(

    monitor="val_loss",
    patience=5,
    restore_best_weights=True

)


# ======================================================
# TRAINING
# ======================================================

print("Training sparse autoencoder...")


history = autoencoder.fit(

    X_train_normal,
    X_train_normal,

    epochs=50,
    batch_size=256,

    validation_data=(
        X_test_normal,
        X_test_normal
    ),

    callbacks=[early_stop],

    shuffle=True,
    verbose=1
)


# ======================================================
# SAVE MODEL
# ======================================================

model_path = (
    MODEL_DIR /
    "sparse_autoencoder.keras"
)

autoencoder.save(
    model_path
)

print(f"\nModel saved to: {model_path}")


# ======================================================
# RECONSTRUCTION ERROR
# ======================================================

print("Calculating reconstruction errors...")


reconstructed = autoencoder.predict(
    X_test,
    verbose=0
)


mse = np.mean(
    np.power(
        X_test - reconstructed,
        2
    ),
    axis=1
)


# ======================================================
# THRESHOLD & METRICS
# ======================================================

print("Calculating threshold from normal test data...")

reconstructed_normal = autoencoder.predict(
    X_test_normal,
    verbose=0
)

mse_normal = np.mean(
    np.power(
        X_test_normal - reconstructed_normal,
        2
    ),
    axis=1
)

threshold = np.percentile(
    mse_normal,
    95
)

print(f"Threshold: {threshold:.6f}")


# Evaluate on full test set
y_pred_anomaly = (mse > threshold).astype(int)
y_test_binary = (y_test > 0).astype(int)

from sklearn.metrics import precision_score, recall_score, f1_score

precision = precision_score(y_test_binary, y_pred_anomaly, zero_division=0)
recall = recall_score(y_test_binary, y_pred_anomaly, zero_division=0)
f1 = f1_score(y_test_binary, y_pred_anomaly, zero_division=0)

print(f"\nAutoencoder Evaluation:")
print(f"Precision: {precision:.4f}")
print(f"Recall:    {recall:.4f}")
print(f"F1 Score:  {f1:.4f}")


# ======================================================
# SAVE THRESHOLD
# ======================================================

with open(
    MODEL_DIR / "threshold.txt",
    "w"
) as f:

    f.write(str(threshold))


# ======================================================
# PLOT LOSS
# ======================================================

plt.figure(figsize=(10, 6))

plt.plot(
    history.history["loss"],
    label="Training Loss"
)

plt.plot(
    history.history["val_loss"],
    label="Validation Loss"
)

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Sparse Autoencoder Loss")
plt.legend()

plt.savefig(
    REPORT_DIR /
    "training_loss.png"
)

plt.close()


# ======================================================
# PLOT RECONSTRUCTION ERROR
# ======================================================

plt.figure(figsize=(10, 6))

plt.hist(
    mse,
    bins=50
)

plt.axvline(
    threshold,
    linestyle="--"
)

plt.xlabel("Reconstruction Error")
plt.ylabel("Frequency")
plt.title("Reconstruction Error Distribution")

plt.savefig(
    REPORT_DIR /
    "reconstruction_error_distribution.png"
)

plt.close()


print("\nSparse autoencoder training completed.")