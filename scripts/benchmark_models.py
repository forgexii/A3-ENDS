import os
import time
import tracemalloc
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
try:
    import seaborn as sns
except ImportError:
    sns = None
import joblib
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, label_binarize
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
try:
    from catboost import CatBoostClassifier
except ImportError:
    CatBoostClassifier = None
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve, auc,
    precision_recall_curve, average_precision_score
)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_PATH = PROJECT_ROOT / "datasets/cleaned_cicids2017/cleaned_cicids2017.csv"
OUTPUT_DIR = PROJECT_ROOT / "reports/benchmark_comparison"
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
    print("[*] Plotting Metrics Comparison Bar Chart (Large Font >= 24px)...")
    metrics_to_plot = ['Accuracy', 'Precision (Macro)', 'Recall (Macro)', 'F1-Score (Macro)', 'ROC-AUC']
    models = results_df['Model'].tolist()

    fig, ax = plt.subplots(figsize=(26, 13))

    x = np.arange(len(metrics_to_plot))
    total_models = len(models)
    bar_width = 0.15
    offsets = np.linspace(-(total_models - 1) / 2 * bar_width, (total_models - 1) / 2 * bar_width, total_models)

    colors = ['#20639B', '#3CAEA3', '#F6D55C', '#ED553B', '#833471']

    for i, model_name in enumerate(models):
        model_row = results_df[results_df['Model'] == model_name].iloc[0]
        vals = [model_row[m] for m in metrics_to_plot]
        bars = ax.bar(x + offsets[i], vals, bar_width, label=model_name, color=colors[i], edgecolor='black', linewidth=1.2)
        
        for bar in bars:
            h = bar.get_height()
            if h > 0.05:
                ax.text(bar.get_x() + bar.get_width() / 2, h + 0.02, f'{h*100:.1f}%' if h <= 1.0 else f'{h:.2f}', 
                        ha='center', va='bottom', fontsize=24, fontweight='bold', rotation=90)

    ax.set_title('Model Evaluation Metrics Comparison', fontsize=32, fontweight='bold', pad=25)
    ax.set_ylabel('Score / Ratio', fontsize=28, fontweight='bold', labelpad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_to_plot, fontsize=24, fontweight='bold')
    ax.tick_params(axis='y', labelsize=24)
    ax.tick_params(axis='x', pad=12)
    ax.set_ylim(0, 1.32)
    ax.grid(axis='y', linestyle='--', alpha=0.5, linewidth=1.2)
    legend = ax.legend(title='Model', bbox_to_anchor=(1.01, 1), loc='upper left', fontsize=24, title_fontsize=26, frameon=True)
    legend.get_title().set_fontweight('bold')

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "metrics_comparison.png", dpi=300, bbox_inches='tight')
    plt.close()
    
def plot_timing_chart(results_df):
    print("[*] Plotting Timing/Memory Comparison...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    
    time_colors = ['#2b5c8f', '#3b78b0', '#4a95d0', '#6baed6', '#9ecae1']
    mem_colors  = ['#a50f15', '#de2d26', '#fb6a4a', '#fc9272', '#fcbba1']

    # 1. Timing
    bars1 = axes[0].bar(results_df['Model'], results_df['Training Time (s)'], color=time_colors, edgecolor='black', linewidth=0.8, width=0.6)
    axes[0].set_title("Training Time Comparison (seconds)", fontsize=13, fontweight='bold', pad=12)
    axes[0].set_ylabel("Training Time (s)", fontsize=11)
    axes[0].grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars1:
        val = bar.get_height()
        axes[0].text(bar.get_x() + bar.get_width() / 2, val + max(results_df['Training Time (s)']) * 0.02,
                     f"{val:.2f} s", ha='center', va='bottom', fontsize=9.5, fontweight='bold')
    axes[0].set_ylim(0, max(results_df['Training Time (s)']) * 1.15)
    axes[0].tick_params(axis='x', rotation=15)
    
    # 2. Memory
    bars2 = axes[1].bar(results_df['Model'], results_df['Peak Memory (MB)'], color=mem_colors, edgecolor='black', linewidth=0.8, width=0.6)
    axes[1].set_title("Peak Memory Usage (MB)", fontsize=13, fontweight='bold', pad=12)
    axes[1].set_ylabel("Peak Memory (MB)", fontsize=11)
    axes[1].grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars2:
        val = bar.get_height()
        label_text = f"{val:.2f} MB" if val < 1.0 else f"{val:.1f} MB"
        axes[1].text(bar.get_x() + bar.get_width() / 2, val + 20,
                     label_text, ha='center', va='bottom',
                     fontsize=9.5, fontweight='bold')
    axes[1].set_ylim(0, max(results_df['Peak Memory (MB)']) * 1.18)
    axes[1].tick_params(axis='x', rotation=15)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "timing_memory_comparison.png", dpi=300)
    plt.close()

def plot_confusion_matrices(models_dict, y_test, label_names):
    print("[*] Plotting Confusion Matrices (Large Font >= 24px, Bold Captions)...")
    
    def clean_label(lbl):
        lbl = str(lbl).replace('\ufffd', '-').replace(' ? ', ' - ')
        while lbl.endswith('?') or lbl.endswith(' '):
            lbl = lbl.rstrip('? ')
        return lbl

    cleaned_label_names = [clean_label(l) for l in label_names]

    for name, data in models_dict.items():
        y_pred = data['y_pred']
        cm = confusion_matrix(y_test, y_pred)
        
        fig, ax = plt.subplots(figsize=(26, 20), dpi=300)
        if sns is not None:
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                        xticklabels=cleaned_label_names, yticklabels=cleaned_label_names,
                        ax=ax,
                        annot_kws={"size": 16, "weight": "bold"},
                        cbar_kws={"label": "Count"})
            cbar = ax.collections[0].colorbar
            cbar.ax.tick_params(labelsize=22)
            cbar.set_label("Count", fontsize=24, fontweight='bold')
        else:
            im = ax.imshow(cm, cmap='Blues')
            cbar = plt.colorbar(im, ax=ax)
            cbar.ax.tick_params(labelsize=22)
            ax.set_xticks(range(len(cleaned_label_names)))
            ax.set_yticks(range(len(cleaned_label_names)))
            
        ax.set_title(f"Confusion Matrix - {name}", fontsize=34, fontweight='bold', pad=25)
        ax.set_ylabel('True Label', fontsize=30, fontweight='bold', labelpad=20)
        ax.set_xlabel('Predicted Label', fontsize=30, fontweight='bold', labelpad=20)
        ax.set_xticklabels(cleaned_label_names, rotation=45, ha='right', rotation_mode='anchor', fontsize=24, fontweight='bold')
        ax.set_yticklabels(cleaned_label_names, fontsize=24, fontweight='bold')
        plt.tight_layout()
        plt.savefig(OUTPUT_DIR / f"confusion_matrix_{name.replace(' ', '_').lower()}.png", dpi=300, bbox_inches='tight')
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
