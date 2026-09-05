"""
Module: Automated Hyperparameter Optimization (Optuna)
Tunes LightGBM tree hyperparameters against temporal validation data to maximize PR-AUC.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Optional, Tuple

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
import yaml

from src.utils import get_project_root, load_config

# Suppress Optuna default logging chatter to keep output clean
optuna.logging.set_verbosity(optuna.logging.WARNING)


def get_tuning_split(
    features_df: pd.DataFrame,
    target_col: str,
    exclude_cols: list,
    val_ratio: float = 0.25,
    embargo_days: int = 5,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame, pd.Series]:
    """
    Creates a temporally ordered train/validation split with an embargo buffer.
    Guarantees that validation data strictly follows training data in time.
    """
    feature_cols = [c for c in features_df.columns if c not in exclude_cols]
    
    min_day = int(features_df["TX_TIME_DAYS"].min())
    max_day = int(features_df["TX_TIME_DAYS"].max())
    total_span = max_day - min_day

    val_span = max(3, int(total_span * val_ratio))
    val_start_day = max_day - val_span
    train_end_day = val_start_day - embargo_days

    # Ensure train_end_day is valid
    if train_end_day <= min_day:
        train_end_day = min_day + max(2, int(total_span * 0.5))
        val_start_day = train_end_day + max(1, embargo_days)

    train_mask = features_df["TX_TIME_DAYS"] <= train_end_day
    val_mask = features_df["TX_TIME_DAYS"] >= val_start_day

    train_df = features_df[train_mask]
    val_df = features_df[val_mask]

    X_train, y_train = train_df[feature_cols], train_df[target_col]
    X_val, y_val = val_df[feature_cols], val_df[target_col]

    return X_train, y_train, X_val, y_val


def objective(
    trial: optuna.Trial,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    base_scale_pos_weight: float,
) -> float:
    """
    Optuna objective function searching LightGBM hyperparameters to maximize PR-AUC.
    """
    num_leaves = trial.suggest_int("num_leaves", 15, 63)
    max_depth = trial.suggest_int("max_depth", 3, 10)
    learning_rate = trial.suggest_float("learning_rate", 0.01, 0.20, log=True)
    min_child_samples = trial.suggest_int("min_child_samples", 20, 100)
    subsample = trial.suggest_float("subsample", 0.60, 0.95)
    colsample_bytree = trial.suggest_float("colsample_bytree", 0.60, 0.95)
    n_estimators = trial.suggest_int("n_estimators", 100, 350, step=50)
    scale_multiplier = trial.suggest_float("scale_pos_weight_multiplier", 0.5, 2.0)

    effective_scale_pos_weight = base_scale_pos_weight * scale_multiplier

    clf = lgb.LGBMClassifier(
        num_leaves=num_leaves,
        max_depth=max_depth,
        learning_rate=learning_rate,
        min_child_samples=min_child_samples,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        n_estimators=n_estimators,
        scale_pos_weight=effective_scale_pos_weight,
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    clf.fit(X_train, y_train)
    y_pred_proba = clf.predict_proba(X_val)[:, 1]

    pr_auc = float(average_precision_score(y_val, y_pred_proba))
    return pr_auc


def run_hyperparameter_tuning(
    features_df: Optional[pd.DataFrame] = None,
    config: Optional[dict] = None,
    n_trials: int = 20,
    timeout: Optional[int] = None,
    update_config: bool = False,
) -> Dict:
    """
    Executes automated Bayesian optimization study using Optuna.
    """
    root = get_project_root()
    if config is None:
        config = load_config()

    if features_df is None:
        feat_path = root / "data" / "processed" / "features.parquet"
        if not feat_path.exists():
            raise FileNotFoundError(f"Features file not found at {feat_path}")
        features_df = pd.read_parquet(feat_path)

    model_cfg = config.get("model", {})
    target_col = model_cfg.get("target_col", "TX_FRAUD")
    exclude_cols = model_cfg.get("exclude_cols_from_features", [])

    print(
        f"\n{'='*75}\n"
        f"  AUTOMATED HYPERPARAMETER OPTIMIZATION (Optuna - {n_trials} Trials)\n"
        f"{'='*75}"
    )

    X_train, y_train, X_val, y_val = get_tuning_split(
        features_df, target_col=target_col, exclude_cols=exclude_cols
    )

    n_pos = int(y_train.sum())
    n_neg = int((y_train == 0).sum())
    base_scale_pos_weight = float(n_neg / n_pos if n_pos > 0 else 1.0)

    print(f"Training split:   {len(X_train)} samples ({y_train.mean()*100:.2f}% fraud)")
    print(f"Validation split: {len(X_val)} samples ({y_val.mean()*100:.2f}% fraud)")
    print(f"Base scale_pos_weight: {base_scale_pos_weight:.2f}")

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler)

    def trial_callback(study: optuna.Study, trial: optuna.trial.FrozenTrial):
        if trial.number == 0 or trial.value >= study.best_value:
            print(f"  Trial {trial.number:>2}: New Best PR-AUC = {trial.value:.4f}")

    study.optimize(
        lambda t: objective(t, X_train, y_train, X_val, y_val, base_scale_pos_weight),
        n_trials=n_trials,
        timeout=timeout,
        callbacks=[trial_callback],
    )

    best_trial = study.best_trial
    raw_params = best_trial.params

    final_lgb_params = {
        "num_leaves": int(raw_params["num_leaves"]),
        "max_depth": int(raw_params["max_depth"]),
        "learning_rate": round(float(raw_params["learning_rate"]), 4),
        "min_child_samples": int(raw_params["min_child_samples"]),
        "subsample": round(float(raw_params["subsample"]), 3),
        "colsample_bytree": round(float(raw_params["colsample_bytree"]), 3),
        "n_estimators": int(raw_params.get("n_estimators", 300)),
        "scale_pos_weight": round(float(base_scale_pos_weight * raw_params.get("scale_pos_weight_multiplier", 1.0)), 2),
        "random_state": 42,
        "n_jobs": -1,
    }

    results = {
        "best_pr_auc": round(float(best_trial.value), 4),
        "best_trial_number": best_trial.number,
        "n_trials_evaluated": len(study.trials),
        "lightgbm_params": final_lgb_params,
        "raw_hyperparameters": raw_params,
    }

    print("\n--- Hyperparameter Optimization Results ---")
    print(f"Best Validation PR-AUC: {results['best_pr_auc']:.4f} (Trial {results['best_trial_number']})")
    print("Optimal LightGBM Hyperparameters:")
    for k, v in final_lgb_params.items():
        print(f"  {k:<20}: {v}")

    # Save to models/best_params.json
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    out_path = models_dir / "best_params.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=4)
    print(f"\nSaved optimal parameters to {out_path}")

    if update_config:
        cfg_path = root / "config.yaml"
        with open(cfg_path, "r") as f:
            cfg_data = yaml.safe_load(f)
        cfg_data["model"]["lightgbm_params"] = final_lgb_params
        with open(cfg_path, "w") as f:
            yaml.dump(cfg_data, f, default_flow_style=False, sort_keys=False)
        print(f"Updated config.yaml with optimal hyperparameters.")

    return results


def main():
    parser = argparse.ArgumentParser(description="Automated Hyperparameter Optimization with Optuna")
    parser.add_argument("--n-trials", type=int, default=20, help="Number of Optuna optimization trials")
    parser.add_argument("--timeout", type=int, default=None, help="Max optimization time in seconds")
    parser.add_argument("--update-config", action="store_true", help="Update config.yaml with best parameters")
    args = parser.parse_args()

    run_hyperparameter_tuning(n_trials=args.n_trials, timeout=args.timeout, update_config=args.update_config)


if __name__ == "__main__":
    main()
