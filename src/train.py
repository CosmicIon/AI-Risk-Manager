import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from src.utils import get_project_root, load_config
import joblib
import json
import time

import argparse
from src.cross_validate import evaluate_walk_forward_cv

def main():
    parser = argparse.ArgumentParser(description="Train Risk Models and Run Walk-Forward CV")
    parser.add_argument("--cv", action="store_true", default=True, help="Run walk-forward purged cross-validation")
    parser.add_argument("--no-cv", dest="cv", action="store_false", help="Skip cross-validation and only train final model")
    args = parser.parse_args()

    print("Running Model Training (Module 4)...")
    config = load_config()
    model_cfg = config['model']
    
    root = get_project_root()
    proc_dir = root / 'data' / 'processed'
    models_dir = root / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_train = {}

    if args.cv:
        print("\n--- Initiating Walk-Forward Cross-Validation ---")
        try:
            cv_summary = evaluate_walk_forward_cv(config=config, save_results=True)
            metrics_train['cross_validation'] = cv_summary
        except Exception as e:
            print(f"Warning: Walk-forward CV could not be executed: {e}")

    print("\nLoading final train data...")
    train = pd.read_parquet(proc_dir / 'train.parquet')
    
    target_col = model_cfg['target_col']
    exclude_cols = model_cfg['exclude_cols_from_features']
    
    features = [c for c in train.columns if c not in exclude_cols]
    
    print(f"Using {len(features)} features for training.")
    
    X_train = train[features]
    y_train = train[target_col]
    
    # Save feature list for inference
    with open(models_dir / 'feature_columns.json', 'w') as f:
        json.dump(features, f, indent=4)
        
    print("Training Logistic Regression Baseline...")
    start_time = time.time()
    lr = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
    lr.fit(X_train, y_train)
    lr_time = time.time() - start_time
    print(f"Logistic Regression trained in {lr_time:.2f}s")
    
    y_pred_lr = lr.predict_proba(X_train)[:, 1]
    metrics_train['baseline_lr'] = {
        'roc_auc': roc_auc_score(y_train, y_pred_lr),
        'pr_auc': average_precision_score(y_train, y_pred_lr)
    }
    joblib.dump(lr, models_dir / 'baseline_lr.pkl')
    
    print("Training LightGBM Primary Model...")
    # Calculate scale_pos_weight
    n_pos = sum(y_train == 1)
    n_neg = sum(y_train == 0)
    scale_pos_weight = n_neg / n_pos if n_pos > 0 else 1.0
    print(f"Calculated scale_pos_weight: {scale_pos_weight:.2f}")
    
    lgb_params = dict(model_cfg['lightgbm_params'])
    lgb_params['scale_pos_weight'] = scale_pos_weight
    lgb_params['verbose'] = -1
    
    start_time = time.time()
    clf = lgb.LGBMClassifier(**lgb_params)
    clf.fit(X_train, y_train)
    lgb_time = time.time() - start_time
    print(f"LightGBM trained in {lgb_time:.2f}s")
    
    y_pred_lgb = clf.predict_proba(X_train)[:, 1]
    metrics_train['lightgbm'] = {
        'roc_auc': roc_auc_score(y_train, y_pred_lgb),
        'pr_auc': average_precision_score(y_train, y_pred_lgb)
    }
    joblib.dump(clf, models_dir / 'model.pkl')
    
    with open(models_dir / 'metrics_train.json', 'w') as f:
        json.dump(metrics_train, f, indent=4)
        
    print("\n--- Training Metrics Summary ---")
    print("Logistic Regression:")
    print(f"  ROC-AUC: {metrics_train['baseline_lr']['roc_auc']:.4f}")
    print(f"  PR-AUC:  {metrics_train['baseline_lr']['pr_auc']:.4f}")
    print("LightGBM:")
    print(f"  ROC-AUC: {metrics_train['lightgbm']['roc_auc']:.4f}")
    print(f"  PR-AUC:  {metrics_train['lightgbm']['pr_auc']:.4f}")
    if 'cross_validation' in metrics_train:
        cv_res = metrics_train['cross_validation']
        print(f"Walk-Forward CV Stability (LightGBM):")
        print(f"  Mean PR-AUC:  {cv_res['lightgbm']['mean_pr_auc']:.4f} +/- {cv_res['lightgbm']['std_pr_auc']:.4f}")
        print(f"  Mean ROC-AUC: {cv_res['lightgbm']['mean_roc_auc']:.4f} +/- {cv_res['lightgbm']['std_roc_auc']:.4f}")
    print("\nTraining complete!")

if __name__ == "__main__":
    main()
