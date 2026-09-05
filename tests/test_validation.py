"""
Unit tests for Purged Walk-Forward Time-Series Cross-Validation (Module 3.1).
Validates strict temporal ordering, embargo purging, zero index overlap, and metric computation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from src.cross_validate import PurgedWalkForwardCV, evaluate_walk_forward_cv


@pytest.fixture
def synthetic_features_60d():
    """Generates synthetic transactions spanning Day 30 to Day 59 (30 days total)."""
    np.random.seed(42)
    n_rows = 600
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
        "TX_FRAUD": np.random.choice([0, 1], size=n_rows, p=[0.9, 0.1]),
    })
    return df


@pytest.fixture
def synthetic_features_180d():
    """Generates synthetic transactions spanning Day 30 to Day 180 (150 days total)."""
    np.random.seed(42)
    n_rows = 1500
    days = np.sort(np.random.randint(30, 181, size=n_rows))
    
    df = pd.DataFrame({
        "TRANSACTION_ID": np.arange(n_rows),
        "TX_DATETIME": pd.date_range("2018-05-01", periods=n_rows, freq="15min"),
        "TX_TIME_DAYS": days,
        "CUSTOMER_ID": np.random.randint(1, 50, size=n_rows),
        "TERMINAL_ID": np.random.randint(1, 100, size=n_rows),
        "TX_AMOUNT": np.random.exponential(50, size=n_rows),
        "TX_AMOUNT_ZSCORE": np.random.normal(0, 1, size=n_rows),
        "TX_DIST_CUSTOMER_TERMINAL": np.random.uniform(0, 50, size=n_rows),
        "CUSTOMER_ID_NB_TX_15MIN_WINDOW": np.random.poisson(1, size=n_rows),
        "CUSTOMER_ID_NB_TX_1HOUR_WINDOW": np.random.poisson(2, size=n_rows),
        "TIME_SINCE_LAST_TX": np.random.uniform(10, 86400, size=n_rows),
        "TX_FRAUD": np.random.choice([0, 1], size=n_rows, p=[0.9, 0.1]),
    })
    return df


def test_walk_forward_strict_temporal_ordering(synthetic_features_60d):
    """Ensure training window is strictly before test window by at least the embargo buffer."""
    cv = PurgedWalkForwardCV(n_splits=3, embargo_days=5)
    splits = list(cv.split(synthetic_features_60d, time_col="TX_TIME_DAYS"))

    assert len(splits) == 3

    for train_idx, test_idx, meta in splits:
        train_days = synthetic_features_60d.iloc[train_idx]["TX_TIME_DAYS"]
        test_days = synthetic_features_60d.iloc[test_idx]["TX_TIME_DAYS"]

        assert len(train_days) > 0
        assert len(test_days) > 0

        # Strict temporal inequality with embargo separation
        assert train_days.max() < test_days.min(), "Train time must be strictly before test time"
        assert test_days.min() - train_days.max() >= 5, (
            f"Gap between train max ({train_days.max()}) and test min ({test_days.min()}) "
            f"must be >= embargo (5)"
        )


def test_walk_forward_zero_leakage_and_embargo_purge(synthetic_features_60d):
    """Ensure zero index overlap and that transactions in embargo window are purged."""
    cv = PurgedWalkForwardCV(n_splits=3, embargo_days=6)
    splits = list(cv.split(synthetic_features_60d, time_col="TX_TIME_DAYS"))

    for train_idx, test_idx, meta in splits:
        set_train = set(train_idx)
        set_test = set(test_idx)

        # Zero index overlap
        overlap = set_train.intersection(set_test)
        assert len(overlap) == 0, f"Found {len(overlap)} overlapping indices between train and test"

        # Embargo purge check
        embargo_start = meta["embargo_start_day"]
        embargo_end = meta["embargo_end_day"]

        embargo_rows = synthetic_features_60d[
            (synthetic_features_60d["TX_TIME_DAYS"] >= embargo_start)
            & (synthetic_features_60d["TX_TIME_DAYS"] <= embargo_end)
        ].index

        # None of the embargo rows should be in train or test
        assert len(set_train.intersection(set(embargo_rows))) == 0
        assert len(set_test.intersection(set(embargo_rows))) == 0


def test_walk_forward_expanding_window_property(synthetic_features_60d):
    """Ensure training size expands monotonically across folds."""
    cv = PurgedWalkForwardCV(n_splits=3, embargo_days=4)
    splits = list(cv.split(synthetic_features_60d, time_col="TX_TIME_DAYS"))

    train_sizes = [len(train_idx) for train_idx, _, _ in splits]
    assert train_sizes[0] < train_sizes[1] < train_sizes[2], "Train set must expand with each fold"


def test_walk_forward_180d_preset(synthetic_features_180d):
    """Verify that a 180-day span triggers the standard enterprise 3-fold rolling schedule."""
    cv = PurgedWalkForwardCV(n_splits=3, embargo_days=7)
    splits = list(cv.split(synthetic_features_180d, time_col="TX_TIME_DAYS"))

    assert len(splits) == 3
    # Verify standard fold definitions
    meta1 = splits[0][2]
    assert meta1["train_start_day"] == 30 and meta1["train_end_day"] == 75
    assert meta1["test_start_day"] == 83 and meta1["test_end_day"] == 105

    meta2 = splits[1][2]
    assert meta2["train_start_day"] == 30 and meta2["train_end_day"] == 110
    assert meta2["test_start_day"] == 118 and meta2["test_end_day"] == 140

    meta3 = splits[2][2]
    assert meta3["train_start_day"] == 30 and meta3["train_end_day"] == 145
    assert meta3["test_start_day"] == 153 and meta3["test_end_day"] == 180


def test_evaluate_walk_forward_cv_execution(synthetic_features_60d):
    """Run full walk-forward evaluation pipeline and verify statistical outputs."""
    summary = evaluate_walk_forward_cv(
        features_df=synthetic_features_60d,
        n_splits=3,
        embargo_days=4,
        save_results=False,
    )

    assert summary["n_folds"] == 3
    assert "baseline_lr" in summary
    assert "lightgbm" in summary
    assert len(summary["folds"]) == 3

    # Metrics validity
    lgb_metrics = summary["lightgbm"]
    assert 0.0 <= lgb_metrics["mean_pr_auc"] <= 1.0
    assert 0.0 <= lgb_metrics["mean_roc_auc"] <= 1.0
    assert lgb_metrics["std_pr_auc"] >= 0.0
    assert lgb_metrics["std_roc_auc"] >= 0.0
