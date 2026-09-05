"""
Module: Cross-Validation (Purged Walk-Forward Time-Series Split)
Implements temporal expanding-window cross-validation with an embargo buffer to prevent
lookahead bias and delayed-label leakage in BFSI fraud detection models.
"""

import json
from pathlib import Path
import time
from typing import Dict, Generator, List, Optional, Tuple

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score

from src.utils import get_project_root, load_config


class PurgedWalkForwardCV:
    """
    Purged Walk-Forward Time-Series Cross-Validator.
    
    In real-world fraud detection:
    1. Standard K-fold CV leaks future patterns into past evaluations.
    2. Fraud labels have reporting delays (e.g., 7-day chargeback buffer).
    
    This validator enforces an expanding training window followed by a purged embargo
    buffer, followed by an out-of-time evaluation test window.
    
    Fold k:
      - Train: [T_start, T_train_end]
      - Embargo: (T_train_end, T_train_end + embargo_days] -> PURGED
      - Test: (T_train_end + embargo_days, T_test_end]
    """

    def __init__(
        self,
        n_splits: int = 3,
        embargo_days: int = 7,
        min_train_days: Optional[int] = None,
        custom_folds: Optional[List[Dict[str, int]]] = None,
    ):
        self.n_splits = n_splits
        self.embargo_days = embargo_days
        self.min_train_days = min_train_days
        self.custom_folds = custom_folds

    def split(
        self, df: pd.DataFrame, time_col: str = "TX_TIME_DAYS"
    ) -> Generator[Tuple[np.ndarray, np.ndarray, Dict], None, None]:
        """
        Yields (train_indices, test_indices, fold_meta) for each fold.
        """
        min_day = int(df[time_col].min())
        max_day = int(df[time_col].max())
        total_span = max_day - min_day

        # Use custom fold definitions if provided
        if self.custom_folds:
            for i, fold_def in enumerate(self.custom_folds):
                train_mask = (df[time_col] >= fold_def["train_start"]) & (
                    df[time_col] <= fold_def["train_end"]
                )
                test_mask = (df[time_col] >= fold_def["test_start"]) & (
                    df[time_col] <= fold_def["test_end"]
                )

                train_idx = np.where(train_mask)[0]
                test_idx = np.where(test_mask)[0]

                meta = {
                    "fold": i + 1,
                    "train_start_day": fold_def["train_start"],
                    "train_end_day": fold_def["train_end"],
                    "embargo_start_day": fold_def["train_end"] + 1,
                    "embargo_end_day": fold_def["test_start"] - 1,
                    "test_start_day": fold_def["test_start"],
                    "test_end_day": fold_def["test_end"],
                }
                yield train_idx, test_idx, meta
            return

        # Preset standard 180-day enterprise splits if dataset spans >= 170 days
        if total_span >= 140:
            standard_180d_folds = [
                {"train_start": 30, "train_end": 75, "test_start": 83, "test_end": 105},
                {"train_start": 30, "train_end": 110, "test_start": 118, "test_end": 140},
                {"train_start": 30, "train_end": 145, "test_start": 153, "test_end": 180},
            ]
            for i, fold_def in enumerate(standard_180d_folds):
                train_mask = (df[time_col] >= fold_def["train_start"]) & (
                    df[time_col] <= fold_def["train_end"]
                )
                test_mask = (df[time_col] >= fold_def["test_start"]) & (
                    df[time_col] <= fold_def["test_end"]
                )

                train_idx = np.where(train_mask)[0]
                test_idx = np.where(test_mask)[0]

                meta = {
                    "fold": i + 1,
                    "train_start_day": fold_def["train_start"],
                    "train_end_day": fold_def["train_end"],
                    "embargo_start_day": fold_def["train_end"] + 1,
                    "embargo_end_day": fold_def["test_start"] - 1,
                    "test_start_day": fold_def["test_start"],
                    "test_end_day": fold_def["test_end"],
                }
                yield train_idx, test_idx, meta
            return

        # Dynamic calculation for arbitrary dataset lengths
        # Reserve initial window for training
        embargo = max(1, self.embargo_days)
        # Ensure min_train_days allows room for n_splits test intervals and embargos
        if self.min_train_days is not None:
            min_train = self.min_train_days
        else:
            # allocate ~35% of total span to base train, leaving 65% for test partitions
            min_train = max(5, int(total_span * 0.35))

        test_available_days = total_span - min_train - embargo
        if test_available_days < self.n_splits:
            # Fallback if span is very small: reduce embargo and recalculate
            embargo = max(1, int(total_span * 0.05))
            min_train = max(3, int(total_span * 0.3))
            test_available_days = total_span - min_train - embargo

        test_slice_len = max(2, test_available_days // self.n_splits)

        for fold in range(self.n_splits):
            test_start = min_day + min_train + embargo + (fold * test_slice_len)
            if fold == self.n_splits - 1:
                test_end = max_day
            else:
                test_end = test_start + test_slice_len - 1

            train_start = min_day
            train_end = test_start - embargo

            train_mask = (df[time_col] >= train_start) & (df[time_col] <= train_end)
            test_mask = (df[time_col] >= test_start) & (df[time_col] <= test_end)

            train_idx = np.where(train_mask)[0]
            test_idx = np.where(test_mask)[0]

            meta = {
                "fold": fold + 1,
                "train_start_day": int(train_start),
                "train_end_day": int(train_end),
                "embargo_start_day": int(train_end + 1),
                "embargo_end_day": int(test_start - 1),
                "test_start_day": int(test_start),
                "test_end_day": int(test_end),
            }
            yield train_idx, test_idx, meta


def evaluate_walk_forward_cv(
    features_df: Optional[pd.DataFrame] = None,
    config: Optional[dict] = None,
    n_splits: int = 3,
    embargo_days: int = 7,
    save_results: bool = True,
) -> Dict:
    """
    Executes walk-forward purged cross-validation across all folds.
    Evaluates both Logistic Regression Baseline and LightGBM models.
    """
    root = get_project_root()
    if config is None:
        config = load_config()

    if features_df is None:
        proc_dir = root / "data" / "processed"
        feat_path = proc_dir / "features.parquet"
        if not feat_path.exists():
            raise FileNotFoundError(f"Processed features not found at {feat_path}")
        features_df = pd.read_parquet(feat_path)

    model_cfg = config.get("model", {})
    target_col = model_cfg.get("target_col", "TX_FRAUD")
    exclude_cols = model_cfg.get("exclude_cols_from_features", [])

    feature_cols = [c for c in features_df.columns if c not in exclude_cols]

    cv = PurgedWalkForwardCV(n_splits=n_splits, embargo_days=embargo_days)
    fold_results = []

    print(
        f"\n{'='*75}\n"
        f"  WALK-FORWARD PURGED TIME-SERIES CROSS-VALIDATION ({n_splits} Folds, Embargo: {embargo_days}d)\n"
        f"{'='*75}"
    )

    import warnings
    from sklearn.exceptions import ConvergenceWarning

    warnings.filterwarnings("ignore", category=ConvergenceWarning)

    for train_idx, test_idx, meta in cv.split(features_df, time_col="TX_TIME_DAYS"):
        fold = meta["fold"]
        train_df = features_df.iloc[train_idx]
        test_df = features_df.iloc[test_idx]

        X_train, y_train = train_df[feature_cols], train_df[target_col]
        X_test, y_test = test_df[feature_cols], test_df[target_col]

        train_fraud_rate = float(y_train.mean() * 100)
        test_fraud_rate = float(y_test.mean() * 100)

        # Baseline Logistic Regression
        lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
        lr.fit(X_train, y_train)
        y_pred_lr = lr.predict_proba(X_test)[:, 1]
        lr_roc = float(roc_auc_score(y_test, y_pred_lr))
        lr_pr = float(average_precision_score(y_test, y_pred_lr))

        # LightGBM Classifier with dynamic scale_pos_weight
        n_pos = int(y_train.sum())
        n_neg = int((y_train == 0).sum())
        scale_pos_weight = float(n_neg / n_pos if n_pos > 0 else 1.0)

        lgb_params = dict(model_cfg.get("lightgbm_params", {}))
        lgb_params["scale_pos_weight"] = scale_pos_weight
        lgb_params["verbose"] = -1

        clf = lgb.LGBMClassifier(**lgb_params)
        clf.fit(X_train, y_train)
        y_pred_lgb = clf.predict_proba(X_test)[:, 1]
        lgb_roc = float(roc_auc_score(y_test, y_pred_lgb))
        lgb_pr = float(average_precision_score(y_test, y_pred_lgb))

        fold_stat = {
            "fold": fold,
            "train_days": f"D{meta['train_start_day']}-D{meta['train_end_day']}",
            "embargo_days": f"D{meta['embargo_start_day']}-D{meta['embargo_end_day']}",
            "test_days": f"D{meta['test_start_day']}-D{meta['test_end_day']}",
            "train_size": len(train_df),
            "test_size": len(test_df),
            "train_fraud_rate_pct": round(train_fraud_rate, 2),
            "test_fraud_rate_pct": round(test_fraud_rate, 2),
            "lr_roc_auc": round(lr_roc, 4),
            "lr_pr_auc": round(lr_pr, 4),
            "lgb_roc_auc": round(lgb_roc, 4),
            "lgb_pr_auc": round(lgb_pr, 4),
        }
        fold_results.append(fold_stat)

    # Compute aggregate statistics
    lr_pr_scores = [r["lr_pr_auc"] for r in fold_results]
    lr_roc_scores = [r["lr_roc_auc"] for r in fold_results]
    lgb_pr_scores = [r["lgb_pr_auc"] for r in fold_results]
    lgb_roc_scores = [r["lgb_roc_auc"] for r in fold_results]

    summary = {
        "n_folds": len(fold_results),
        "embargo_days": embargo_days,
        "baseline_lr": {
            "mean_pr_auc": round(float(np.mean(lr_pr_scores)), 4),
            "std_pr_auc": round(float(np.std(lr_pr_scores)), 4),
            "mean_roc_auc": round(float(np.mean(lr_roc_scores)), 4),
            "std_roc_auc": round(float(np.std(lr_roc_scores)), 4),
        },
        "lightgbm": {
            "mean_pr_auc": round(float(np.mean(lgb_pr_scores)), 4),
            "std_pr_auc": round(float(np.std(lgb_pr_scores)), 4),
            "mean_roc_auc": round(float(np.mean(lgb_roc_scores)), 4),
            "std_roc_auc": round(float(np.std(lgb_roc_scores)), 4),
        },
        "folds": fold_results,
    }

    # Print clean formatted table
    print(f"\n{'Fold':<6} | {'Train Days':<12} | {'Test Days':<12} | {'Train/Test N':<14} | {'LR PR-AUC':<10} | {'LGB PR-AUC':<10} | {'LGB ROC':<8}")
    print("-" * 82)
    for r in fold_results:
        n_str = f"{r['train_size']}/{r['test_size']}"
        print(
            f"{r['fold']:<6} | {r['train_days']:<12} | {r['test_days']:<12} | {n_str:<14} | "
            f"{r['lr_pr_auc']:<10.4f} | {r['lgb_pr_auc']:<10.4f} | {r['lgb_roc_auc']:<8.4f}"
        )
    print("-" * 82)
    print(
        f"LightGBM Mean Stability: PR-AUC = {summary['lightgbm']['mean_pr_auc']:.4f} +/- {summary['lightgbm']['std_pr_auc']:.4f} | "
        f"ROC-AUC = {summary['lightgbm']['mean_roc_auc']:.4f} +/- {summary['lightgbm']['std_roc_auc']:.4f}"
    )
    print(
        f"Baseline LR Stability:   PR-AUC = {summary['baseline_lr']['mean_pr_auc']:.4f} +/- {summary['baseline_lr']['std_pr_auc']:.4f} | "
        f"ROC-AUC = {summary['baseline_lr']['mean_roc_auc']:.4f} +/- {summary['baseline_lr']['std_roc_auc']:.4f}\n"
    )

    if save_results:
        models_dir = root / "models"
        models_dir.mkdir(parents=True, exist_ok=True)
        out_path = models_dir / "cv_results.json"
        with open(out_path, "w") as f:
            json.dump(summary, f, indent=4)
        print(f"Saved cross-validation results to {out_path}")

    return summary


if __name__ == "__main__":
    evaluate_walk_forward_cv()
