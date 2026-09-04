"""
Unit tests for Data Ingestion & Adapters (Module 6 - Vectorized Simulation & Real-World Adapters).
Validates vectorized distance computation, Kaggle adapter, IEEE-CIS adapter, and schema contracts.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from src.adapters.kaggle import KaggleCreditCardAdapter, generate_sample_kaggle_data
from src.adapters.ieee_cis import IEEECISAdapter, generate_sample_ieee_cis_data
from src.ingestion import (
    compute_available_terminals_vectorized,
    generate_customer_profiles_table,
    generate_terminal_profiles_table,
)


def test_vectorized_available_terminals_computation():
    """Verify vectorized 2D distance broadcasting correctly matches terminals within radius."""
    cust_df = generate_customer_profiles_table(10, random_state=42)
    term_df = generate_terminal_profiles_table(20, random_state=42)

    available = compute_available_terminals_vectorized(cust_df, term_df, r=15.0)

    assert len(available) == len(cust_df)
    for i, term_list in enumerate(available):
        assert isinstance(term_list, list)
        assert len(term_list) > 0  # Fallback guarantees at least 1 terminal
        
        # Verify actual distances
        cx, cy = cust_df.loc[i, ["x_customer_id", "y_customer_id"]].values
        for tid in term_list:
            tx, ty = term_df.loc[tid, ["x_terminal_id", "y_terminal_id"]].values
            dist = np.sqrt((cx - tx) ** 2 + (cy - ty) ** 2)
            # Either distance < radius or fallback was assigned
            assert dist < 15.0 or len(term_list) == 1


def test_kaggle_credit_card_adapter_transform():
    """Verify Kaggle adapter standardizes raw benchmark data into unified risk schema."""
    raw_df = generate_sample_kaggle_data(n_samples=150, random_state=42)
    adapter = KaggleCreditCardAdapter(start_date="2018-04-01", n_customers=30, n_terminals=50)

    standardized = adapter.transform(raw_df)

    # Check required columns
    expected_cols = [
        "TRANSACTION_ID",
        "TX_DATETIME",
        "TX_TIME_DAYS",
        "TX_TIME_SECONDS",
        "CUSTOMER_ID",
        "TERMINAL_ID",
        "TX_AMOUNT",
        "TX_FRAUD",
    ]
    for col in expected_cols:
        assert col in standardized.columns

    assert len(standardized) == 150
    assert standardized["TX_FRAUD"].isin([0, 1]).all()
    assert (standardized["TX_AMOUNT"] > 0).all()
    assert standardized["TX_DATETIME"].is_monotonic_increasing
    assert standardized[expected_cols].isnull().sum().sum() == 0


def test_ieee_cis_adapter_transform():
    """Verify IEEE-CIS adapter standardizes benchmark data into unified risk schema."""
    raw_df = generate_sample_ieee_cis_data(n_samples=150, random_state=42)
    adapter = IEEECISAdapter(start_date="2018-04-01", n_customers=25, n_terminals=40)

    standardized = adapter.transform(raw_df)

    expected_cols = [
        "TRANSACTION_ID",
        "TX_DATETIME",
        "TX_TIME_DAYS",
        "TX_TIME_SECONDS",
        "CUSTOMER_ID",
        "TERMINAL_ID",
        "TX_AMOUNT",
        "TX_FRAUD",
    ]
    for col in expected_cols:
        assert col in standardized.columns

    assert len(standardized) == 150
    assert standardized["TX_FRAUD"].isin([0, 1]).all()
    assert (standardized["TX_AMOUNT"] > 0).all()
    assert standardized["TX_DATETIME"].is_monotonic_increasing
    assert standardized[expected_cols].isnull().sum().sum() == 0


def test_adapter_validation_error_on_corrupt_data():
    """Ensure adapter rejects corrupt schemas missing required columns or negative amounts."""
    adapter = KaggleCreditCardAdapter()

    # Missing Amount
    bad_df1 = pd.DataFrame({"Time": [100], "Class": [0]})
    with pytest.raises(KeyError):
        adapter.transform(bad_df1)

    # Corrupt validation directly
    bad_out = pd.DataFrame({
        "TRANSACTION_ID": [1],
        "TX_DATETIME": [pd.Timestamp.now()],
        "TX_TIME_DAYS": [0],
        "TX_TIME_SECONDS": [100],
        "CUSTOMER_ID": [1],
        "TERMINAL_ID": [1],
        "TX_AMOUNT": [-20.0],  # Negative amount!
        "TX_FRAUD": [0],
    })
    with pytest.raises(ValueError, match="Negative transaction amounts"):
        adapter.validate(bad_out)
