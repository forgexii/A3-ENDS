'''Train a sparse autoencoder on the CICIDS2017 dataset and evaluate its performance.'''
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf

from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Input,
    Dense
)

from tensorflow.keras.regularizers import l1

from tensorflow.keras.callbacks import (
    EarlyStopping
)

from tensorflow.keras.models import load_model

from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
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
    "features/CICIDS2017"
)

AUTOENCODER_DIR = (
    MODELS_DIR /
    "autoencoder"
)

AUTOENCODER_DIR.mkdir(
    parents=True,
    exist_ok=True
)

REPORT_DIR = (
    REPORTS_DIR /
    "autoencoder"
)

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ======================================================
# LOAD DATA
# ======================================================

print("Loading feature arrays...")

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
# EXTRACT NORMAL TRAFFIC
# ======================================================

print("Extracting normal traffic...")

normal_class = 0

X_train_normal = X_train[
    y_train == normal_class
]

print(f"Normal samples: {X_train_normal.shape[0]}")


# ======================================================
# MODEL ARCHITECTURE
# ======================================================

print("Building sparse autoencoder...")

input_dim = X_train.shape[1]

input_layer = Input(
    shape=(input_dim,)
)


# Encoder
encoded = Dense(
    64,
    activation="relu",
    activity_regularizer=l1(1e-5)
)(input_layer)

encoded = Dense(
    32,
    activation="relu",
    activity_regularizer=l1(1e-5)
)(encoded)

encoded = Dense(
    16,
    activation="relu",
    activity_regularizer=l1(1e-5)
)(encoded)


# Decoder
decoded = Dense(
    32,
    activation="relu"
)(encoded)

decoded = Dense(
    64,
    activation="relu"
)(decoded)

decoded = Dense(
    input_dim,
    activation="sigmoid"
)(decoded)


# Autoencoder model
autoencoder = Model(
    input_layer,
    decoded
)


# ======================================================
# COMPILE MODEL
# ======================================================

print("Compiling model...")

autoencoder.compile(
    optimizer="adam",
    loss="mse"
)


# ======================================================
# EARLY STOPPING
# ======================================================

early_stopping = EarlyStopping(
    monitor="val_loss",
    patience=5,
    restore_best_weights=True
)


# ======================================================
# TRAIN MODEL
# ======================================================

print("Training sparse autoencoder...")

history = autoencoder.fit(
    X_train_normal,
    X_train_normal,
    epochs=30,
    batch_size=256,
    validation_split=0.2,
    shuffle=True,
    callbacks=[early_stopping],
    verbose=1
)


# ======================================================
# SAVE MODEL
# ======================================================

print("Saving model...")

autoencoder.save(
    AUTOENCODER_DIR /
    "sparse_autoencoder.keras"
)

print("Model saved successfully.")


# ======================================================
# TRAINING LOSS PLOT
# ======================================================

print("Generating training loss plot...")

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

plt.title(
    "Sparse Autoencoder Training Loss"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    REPORT_DIR /
    "training_loss.png",
    bbox_inches="tight",
    dpi=120
)

plt.close()


# ======================================================
# RECONSTRUCTION
# ======================================================

print("Generating reconstructions...")

X_test_pred = autoencoder.predict(
    X_test
)


# ======================================================
# RECONSTRUCTION ERROR
# ======================================================

print("Calculating reconstruction error...")

mse = np.mean(
    np.power(
        X_test - X_test_pred,
        2
    ),
    axis=1
)


# ======================================================
# THRESHOLD
# ======================================================

threshold = np.percentile(
    mse,
    95
)

print(f"Anomaly Threshold: {threshold}")


# ======================================================
# PREDICTIONS
# ======================================================

y_pred = (
    mse > threshold
).astype(int)


# ======================================================
# CONVERT LABELS
# ======================================================

y_test_binary = (
    y_test != normal_class
).astype(int)


# ======================================================
# METRICS
# ======================================================

precision = precision_score(
    y_test_binary,
    y_pred
)

recall = recall_score(
    y_test_binary,
    y_pred
)

f1 = f1_score(
    y_test_binary,
    y_pred
)


print("\nAutoencoder Evaluation")

print(f"Precision: {precision:.4f}")
print(f"Recall: {recall:.4f}")
print(f"F1-Score: {f1:.4f}")


# ======================================================
# SAVE METRICS
# ======================================================

with open(
    REPORT_DIR / "metrics.txt",
    "w"
) as f:

    f.write(
        f"Precision: {precision:.4f}\n"
    )

    f.write(
        f"Recall: {recall:.4f}\n"
    )

    f.write(
        f"F1-Score: {f1:.4f}\n"
    )

    f.write(
        f"Threshold: {threshold:.6f}\n"
    )


# ======================================================
# RECONSTRUCTION ERROR PLOT
# ======================================================

print("Generating reconstruction error plot...")

plt.figure(figsize=(10, 6))

plt.hist(
    mse,
    bins=100
)

plt.axvline(
    threshold,
    linestyle="--"
)

plt.xlabel(
    "Reconstruction Error"
)

plt.ylabel(
    "Frequency"
)

plt.title(
    "Autoencoder Reconstruction Error"
)

plt.tight_layout()

plt.savefig(
    REPORT_DIR /
    "reconstruction_error.png",
    bbox_inches="tight",
    dpi=120
)

plt.close()


print("\nSparse autoencoder pipeline completed.")