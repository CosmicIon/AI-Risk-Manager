"""
Unit tests for Feature Leakage & Temporal Boundary Invariants (Module 7.1).
Guarantees zero future data leakage, strict 7-day delay embargo enforcement,
and absolute train/test dataset isolation.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from src.features import get_count_risk_rolling_window, get_customer_spending_behaviours_features
from src.utils import get_project_root


def test_terminal_delay_embargo_strictly_enforces_delay():
    """
    Verify that terminal risk calculated at day T strictly includes fraud labels
    from <= T - delay_period (7 days), and never looks ahead into recent unreported frauds.
    """
    delay_period = 7
    base_time = pd.Timestamp("2018-04-01 12:00:00")
    
    # Construct a sequence of transactions for Terminal 99
    # Day 0 to Day 20: 1 transaction per day
    records = []
    for day in range(25):
        records.append({
            "TRANSACTION_ID": day,
            "TX_DATETIME": base_time + pd.Timedelta(days=day),
            "CUSTOMER_ID": day % 5,
            "TERMINAL_ID": 99,
            "TX_AMOUNT": 50.0,
            # Single fraud occurs at Day 10
            "TX_FRAUD": 1 if day == 10 else 0,
        })
    df = pd.DataFrame(records)

    # Compute rolling window features with delay_period = 7 and window = 7 days
    result = get_count_risk_rolling_window(
        df, delay_period=delay_period, windows_size_in_days=[7]
    )

    # For days 0 to 16 (Day 10 + 6 days = Day 16):
    # The fraud on Day 10 must NOT appear in the risk calculation
    # Because (Day_i - delay_period) <= 16 - 7 = 9 < 10
    mask_before_reporting = result["TX_DATETIME"] < (base_time + pd.Timedelta(days=17))
    risk_before = result.loc[mask_before_reporting, "TERMINAL_ID_RISK_7DAY_WINDOW"]
    assert (risk_before == 0.0).all(), (
        f"Found non-zero risk before 7-day reporting delay elapsed! Max risk: {risk_before.max()}"
    )

    # On Day 17 (Day 10 + 7):
    # The fraud from Day 10 is now reported (10 <= 17 - 7)
    # The risk on Day 17 must be > 0
    row_day_17 = result[result["TX_DATETIME"] == (base_time + pd.Timedelta(days=17))]
    assert len(row_day_17) == 1
    assert row_day_17["TERMINAL_ID_RISK_7DAY_WINDOW"].values[0] > 0.0, (
        "Expected reported fraud to be incorporated on Day 17 (Day 10 + 7-day delay)"
    )


def test_customer_rolling_features_have_no_future_leakage():
    """
    Verify customer rolling windows (1d, 7d, 30d) strictly aggregate backward in time
    and never incorporate transactions from future timestamps.
    """
    base_time = pd.Timestamp("2018-05-01 10:00:00")
    txs = pd.DataFrame({
        "CUSTOMER_ID": [1, 1, 1, 1],
        "TX_DATETIME": [
            base_time,                                # Day 0: $10
            base_time + pd.Timedelta(hours=2),        # Day 0 (+2h): $20
            base_time + pd.Timedelta(days=2),         # Day 2: $100
            base_time + pd.Timedelta(days=5),         # Day 5: $1000 (huge future spike)
        ],
        "TX_AMOUNT": [10.0, 20.0, 100.0, 1000.0],
    })

    result = get_customer_spending_behaviours_features(txs, windows_size_in_days=[1, 7, 30])

    # At row 0: only row 0 exists. 1d count = 1, avg = 10
    assert result.loc[0, "CUSTOMER_ID_NB_TX_1DAY_WINDOW"] == 1
    assert result.loc[0, "CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW"] == 10.0

    # At row 1: row 0 and 1 exist. 1d count = 2, avg = 15
    assert result.loc[1, "CUSTOMER_ID_NB_TX_1DAY_WINDOW"] == 2
    assert result.loc[1, "CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW"] == 15.0

    # At row 2: row 3 ($1000 at Day 5) must NOT affect row 2
    assert result.loc[2, "CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW"] < 50.0, (
        f"Future transaction of $1000 leaked into row 2! Avg: {result.loc[2, 'CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW']}"
    )


def test_train_test_split_temporal_isolation_and_zero_overlap():
    """
    Verify that the production train.parquet and test.parquet datasets have:
    1. Zero index or TRANSACTION_ID overlap.
    2. Strict temporal separation: max(Train Day) < min(Test Day).
    """
    root = get_project_root()
    proc_dir = root / "data" / "processed"
    train_path = proc_dir / "train.parquet"
    test_path = proc_dir / "test.parquet"

    if not train_path.exists() or not test_path.exists():
        pytest.skip("Train or test parquet file not found; skipping integration check.")

    train_df = pd.read_parquet(train_path)
    test_df = pd.read_parquet(test_path)

    # Zero overlap in transaction IDs
    train_ids = set(train_df["TRANSACTION_ID"])
    test_ids = set(test_df["TRANSACTION_ID"])
    overlap = train_ids.intersection(test_ids)
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping transaction IDs between train and test!"

    # Strict temporal boundary
    max_train_day = train_df["TX_TIME_DAYS"].max()
    min_test_day = test_df["TX_TIME_DAYS"].min()
    assert max_train_day < min_test_day, (
        f"Temporal leakage detected: max train day ({max_train_day}) >= min test day ({min_test_day})"
    )
