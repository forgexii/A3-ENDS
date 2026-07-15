import os
import time
import tracemalloc
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve, auc,
    precision_recall_curve, average_precision_score
)

# Constants
DATASET_PATH = "datasets/cleaned_cicids2017/cleaned_cicids2017.csv"
OUTPUT_DIR = Path("reports/benchmark_comparison")
SAMPLE_FRACTION = 0.50  # 50% sample to speed up Random Forest on 1.8M rows

def setup_directories():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_and_preprocess_data():
    print(f"[*] Loading dataset from {DATASET_PATH}...")
    df = pd.read_csv(DATASET_PATH)
    
    # Stratified Sampling to keep class ratios intact but speed up training
    if 0.0 < SAMPLE_FRACTION < 1.0:
        print(f"[*] Applying {SAMPLE_FRACTION*100}% stratified sampling...")
        df = df.groupby('Label').sample(frac=SAMPLE_FRACTION, random_state=42)
    print(f"[*] Sampled dataset size: {len(df)} rows")
    
    # Separate features and target
    y = df['Label']
    X = df.drop(columns=['Label'])
    
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    # Train-test split (80-20)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )
    
    return X_train, X_test, y_train, y_test, le, X.columns.tolist()

def train_and_evaluate(name, model, X_train, y_train, X_test, y_test, num_classes):
    print(f"\n========================================")
    print(f"[*] Training {name}...")
    print(f"========================================")
    
    # Tracking Memory & Training Time
    tracemalloc.start()
    train_start = time.time()
    
    model.fit(X_train, y_train)
    
    train_end = time.time()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    train_time = train_end - train_start
    peak_mem_mb = peak_mem / (1024 * 1024)
    print(f"[+] Training Time: {train_time:.2f}s | Peak Memory: {peak_mem_mb:.2f} MB")
    
    # Tracking Prediction Time
    pred_start = time.time()
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    pred_end = time.time()
    pred_time = pred_end - pred_start
    
    # Calculate Metrics
    print("[*] Calculating Metrics...")
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average='macro', zero_division=0)
    rec = recall_score(y_test, y_pred, average='macro', zero_division=0)
    f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
    
    try:
        roc_auc = roc_auc_score(y_test, y_proba, multi_class='ovr', average='macro')
    except Exception as e:
        roc_auc = 0.0
        print(f"[-] Warning: Could not calculate ROC-AUC: {e}")
        
    metrics = {
        "Model": name,
        "Accuracy": acc,
        "Precision (Macro)": prec,
        "Recall (Macro)": rec,
        "F1-Score (Macro)": f1,
        "ROC-AUC": roc_auc,
        "Training Time (s)": train_time,
        "Prediction Time (s)": pred_time,
        "Peak Memory (MB)": peak_mem_mb
    }
    
    # Get Feature Importances
    importances = None
    if hasattr(model, 'feature_importances_'):
        importances = model.feature_importances_
        
    return metrics, y_pred, y_proba, importances

def plot_bar_chart(results_df):
    print("[*] Plotting Metrics Comparison Bar Chart...")
    metrics_to_plot = ['Accuracy', 'Precision (Macro)', 'Recall (Macro)', 'F1-Score (Macro)']
    
    df_melted = pd.melt(results_df, id_vars=['Model'], value_vars=metrics_to_plot, 
                        var_name='Metric', value_name='Score')
    
    plt.figure(figsize=(12, 6))
    sns.barplot(x='Metric', y='Score', hue='Model', data=df_melted, palette='viridis')
    plt.title("Model Evaluation Metrics Comparison", fontsize=16)
    plt.ylim(0, 1.1)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "metrics_comparison.png")
    plt.close()
    
def plot_timing_chart(results_df):
    print("[*] Plotting Timing/Memory Comparison...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Timing
    sns.barplot(x='Model', y='Training Time (s)', data=results_df, ax=axes[0], palette='Blues_r')
    axes[0].set_title("Training Time Comparison (seconds)")
    
    # Memory
    sns.barplot(x='Model', y='Peak Memory (MB)', data=results_df, ax=axes[1], palette='Reds_r')
    axes[1].set_title("Peak Memory Usage (MB)")
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "timing_memory_comparison.png")
    plt.close()

def plot_confusion_matrices(models_dict, y_test, label_names):
    print("[*] Plotting Confusion Matrices...")
    for name, data in models_dict.items():
        y_pred = data['y_pred']
        cm = confusion_matrix(y_test, y_pred)
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                    xticklabels=label_names, yticklabels=label_names)
        plt.title(f"Confusion Matrix - {name}")
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"confusion_matrix_{name.replace(' ', '_').lower()}.png")
        plt.close()

def plot_roc_curves(models_dict, y_test, num_classes, label_names):
    print("[*] Plotting ROC Curves (Macro-Average)...")
    y_test_bin = label_binarize(y_test, classes=range(num_classes))
    
    plt.figure(figsize=(10, 8))
    
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    
    for (name, data), color in zip(models_dict.items(), colors):
        y_proba = data['y_proba']
        
        # Calculate macro-average ROC for this model
        fpr = dict()
        tpr = dict()
        roc_auc = dict()
        for i in range(num_classes):
            fpr[i], tpr[i], _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
            roc_auc[i] = auc(fpr[i], tpr[i])
            
        all_fpr = np.unique(np.concatenate([fpr[i] for i in range(num_classes)]))
        mean_tpr = np.zeros_like(all_fpr)
        for i in range(num_classes):
            mean_tpr += np.interp(all_fpr, fpr[i], tpr[i])
        mean_tpr /= num_classes
        
        macro_auc = auc(all_fpr, mean_tpr)
        plt.plot(all_fpr, mean_tpr, color=color, lw=2, label=f'{name} (macro AUC = {macro_auc:.3f})')
        
    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('Macro-Average ROC Curve Comparison')
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "roc_curves.png")
    plt.close()
    
def plot_precision_recall_curves(models_dict, y_test, num_classes):
    print("[*] Plotting Precision-Recall Curves (Macro-Average)...")
    y_test_bin = label_binarize(y_test, classes=range(num_classes))
    
    plt.figure(figsize=(10, 8))
    colors = ['blue', 'green', 'red', 'orange', 'purple']
    
    for (name, data), color in zip(models_dict.items(), colors):
        y_proba = data['y_proba']
        
        precision = dict()
        recall = dict()
        average_precision = dict()
        for i in range(num_classes):
            precision[i], recall[i], _ = precision_recall_curve(y_test_bin[:, i], y_proba[:, i])
            average_precision[i] = average_precision_score(y_test_bin[:, i], y_proba[:, i])
            
        # Approximation for macro-average PR curve
        precision["macro"], recall["macro"], _ = precision_recall_curve(y_test_bin.ravel(), y_proba.ravel())
        ap = average_precision_score(y_test_bin, y_proba, average="macro")
        
        plt.plot(recall["macro"], precision["macro"], color=color, lw=2, label=f'{name} (macro AP = {ap:.3f})')
        
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title('Macro-Average Precision-Recall Curve Comparison')
    plt.legend(loc="lower left")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "precision_recall_curves.png")
    plt.close()

def plot_feature_importance(models_dict, feature_names):
    print("[*] Plotting Feature Importance Comparison...")
    
    # Filter only models that have importances (tree based)
    tree_models = {k: v for k, v in models_dict.items() if v['importances'] is not None}
    
    if not tree_models:
        return
        
    fig, axes = plt.subplots(1, len(tree_models), figsize=(18, 8))
    # If there's only 1 tree model, axes isn't an array
    if len(tree_models) == 1:
        axes = [axes]
    
    for idx, (name, data) in enumerate(tree_models.items()):
        importances = data['importances']
            
        # Get top 15 features
        indices = np.argsort(importances)[::-1][:15]
        
        sns.barplot(x=importances[indices], y=[feature_names[i] for i in indices], ax=axes[idx], palette='crest')
        axes[idx].set_title(f'Top 15 Features - {name}')
        axes[idx].set_xlabel('Relative Importance')
        
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "feature_importance.png")
    plt.close()

def main():
    setup_directories()
    
    X_train, X_test, y_train, y_test, le, feature_names = load_and_preprocess_data()
    num_classes = len(le.classes_)
    
    models_to_train = {
        "Decision Tree": DecisionTreeClassifier(random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=100, n_jobs=-1, random_state=42),
        "XGBoost": XGBClassifier(n_estimators=100, use_label_encoder=False, eval_metric='mlogloss', n_jobs=-1, random_state=42),
        "LightGBM": LGBMClassifier(n_estimators=100, n_jobs=-1, random_state=42),
        "CatBoost": CatBoostClassifier(iterations=100, thread_count=-1, random_seed=42, verbose=False)
    }
    
    all_results = []
    models_data = {}
    
    for name, model in models_to_train.items():
        metrics, y_pred, y_proba, importances = train_and_evaluate(
            name, model, X_train, y_train, X_test, y_test, num_classes
        )
        all_results.append(metrics)
        models_data[name] = {
            'y_pred': y_pred,
            'y_proba': y_proba,
            'importances': importances
        }
        
        # Save the trained model
        safe_name = name.replace(" ", "_").lower()
        model_dir = Path(f"models/{safe_name}")
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_dir / f"{safe_name}_model.pkl")
        print(f"[*] Saved {name} model to {model_dir}/{safe_name}_model.pkl")
        
    # Save raw results
    print("\n[*] Saving results to CSV/JSON...")
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(OUTPUT_DIR / "benchmark_results.csv", index=False)
    results_df.to_json(OUTPUT_DIR / "benchmark_results.json", orient='records', indent=4)
    
    print("\n" + "="*50)
    print("FINAL METRICS:")
    print("="*50)
    print(results_df.to_string(index=False))
    
    # Generate Visualizations
    plot_bar_chart(results_df)
    plot_timing_chart(results_df)
    plot_confusion_matrices(models_data, y_test, list(le.classes_))
    plot_roc_curves(models_data, y_test, num_classes, list(le.classes_))
    plot_precision_recall_curves(models_data, y_test, num_classes)
    plot_feature_importance(models_data, feature_names)
    
    print(f"\n[+] All benchmarking complete! Check the '{OUTPUT_DIR}' folder for results and charts.")

if __name__ == "__main__":
    main()
