import joblib
import numpy as np
from xgboost import XGBClassifier
from pathlib import Path

# Paths
REALTIME_DIR = Path("datasets/realtime_features/CICIDS2017")
MODELS_DIR = Path("models/xgboost")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

print("[*] Loading realtime feature arrays...")
X_train = np.load(REALTIME_DIR / "X_train.npy")
y_train = np.load(REALTIME_DIR / "y_train.npy")
X_test = np.load(REALTIME_DIR / "X_test.npy")
y_test = np.load(REALTIME_DIR / "y_test.npy")

print(f"[*] X_train shape: {X_train.shape}")
print(f"[*] y_train shape: {y_train.shape}")

print("[*] Training XGBoost on realtime 6-feature subset...")
model = XGBClassifier(
    n_estimators=100,
    use_label_encoder=False,
    eval_metric='mlogloss',
    n_jobs=-1,
    random_state=42
)

model.fit(X_train, y_train)

score = model.score(X_test, y_test)
print(f"[+] Realtime Accuracy: {score * 100:.2f}%")

model_path = MODELS_DIR / "xgboost_model.pkl"
joblib.dump(model, model_path)
print(f"[+] Saved realtime XGBoost model to {model_path}")
