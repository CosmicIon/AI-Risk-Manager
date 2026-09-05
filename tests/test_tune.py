"""
Unit tests for Automated Hyperparameter Optimization (Module 3.2).
Validates temporal split generation, Optuna objective function, and end-to-end tuning pipeline.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import optuna
import pandas as pd
import pytest

from src.tune import get_tuning_split, objective, run_hyperparameter_tuning


@pytest.fixture
def synthetic_tuning_data():
    """Generates synthetic transactions spanning Day 30 to Day 60."""
    np.random.seed(42)
    n_rows = 500
    days = np.sort(np.random.randint(30, 60, size=n_rows))

    df = pd.DataFrame({
        "TRANSACTION_ID": np.arange(n_rows),
        "TX_DATETIME": pd.date_range("2018-05-01", periods=n_rows, freq="30min"),
        "TX_TIME_DAYS": days,
        "CUSTOMER_ID": np.random.randint(1, 50, size=n_rows),
        "TERMINAL_ID": np.random.randint(1, 100, size=n_rows),
        "TX_AMOUNT": np.random.exponential(50, size=n_rows),
        "TX_AMOUNT_ZSCORE": np.random.normal(0, 1, size=n_rows),
        "TX_DIST_CUSTOMER_TERMINAL": np.random.uniform(0, 50, size=n_rows),
        "CUSTOMER_ID_NB_TX_15MIN_WINDOW": np.random.poisson(1, size=n_rows),
        "CUSTOMER_ID_NB_TX_1HOUR_WINDOW": np.random.poisson(2, size=n_rows),
        "TIME_SINCE_LAST_TX": np.random.uniform(10, 86400, size=n_rows),
        "TX_FRAUD": np.random.choice([0, 1], size=n_rows, p=[0.85, 0.15]),
    })
    return df


def test_tuning_split_temporal_ordering_and_embargo(synthetic_tuning_data):
    """Ensure training window is strictly before validation window with embargo separation."""
    embargo = 5
    exclude = ["TRANSACTION_ID", "TX_DATETIME", "CUSTOMER_ID", "TERMINAL_ID", "TX_FRAUD"]
    X_train, y_train, X_val, y_val = get_tuning_split(
        synthetic_tuning_data,
        target_col="TX_FRAUD",
        exclude_cols=exclude,
        val_ratio=0.25,
        embargo_days=embargo,
    )

    assert len(X_train) > 0
    assert len(X_val) > 0
    assert len(y_train) == len(X_train)
    assert len(y_val) == len(X_val)

    # Check temporal ordering
    train_days = synthetic_tuning_data.loc[X_train.index, "TX_TIME_DAYS"]
    val_days = synthetic_tuning_data.loc[X_val.index, "TX_TIME_DAYS"]

    assert train_days.max() < val_days.min(), "Train time must strictly precede validation time"
    assert val_days.min() - train_days.max() >= embargo, f"Gap must be at least {embargo} days"

    # Check zero index overlap
    overlap = set(X_train.index).intersection(set(X_val.index))
    assert len(overlap) == 0


def test_objective_function_scoring(synthetic_tuning_data):
    """Ensure the Optuna objective function returns a valid PR-AUC score in [0.0, 1.0]."""
    exclude = ["TRANSACTION_ID", "TX_DATETIME", "CUSTOMER_ID", "TERMINAL_ID", "TX_FRAUD"]
    X_train, y_train, X_val, y_val = get_tuning_split(
        synthetic_tuning_data,
        target_col="TX_FRAUD",
        exclude_cols=exclude,
        val_ratio=0.25,
        embargo_days=4,
    )

    base_scale = float((y_train == 0).sum() / max(1, y_train.sum()))

    study = optuna.create_study(direction="maximize")
    trial = study.ask()

    score = objective(trial, X_train, y_train, X_val, y_val, base_scale)

    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


def test_run_hyperparameter_tuning_end_to_end(synthetic_tuning_data):
    """Verify complete tuning pipeline produces valid parameters and metrics."""
    res = run_hyperparameter_tuning(
        features_df=synthetic_tuning_data,
        n_trials=2,
        update_config=False,
    )

    assert "best_pr_auc" in res
    assert 0.0 <= res["best_pr_auc"] <= 1.0
    assert res["n_trials_evaluated"] == 2
    assert "lightgbm_params" in res

    params = res["lightgbm_params"]
    assert 15 <= params["num_leaves"] <= 63
    assert 3 <= params["max_depth"] <= 10
    assert 0.01 <= params["learning_rate"] <= 0.20
    assert 20 <= params["min_child_samples"] <= 100
    assert 0.60 <= params["subsample"] <= 0.95
    assert 0.60 <= params["colsample_bytree"] <= 0.95
    assert params["n_estimators"] >= 100
