"""
Module: Kaggle Credit Card Fraud Dataset Adapter
Converts raw Kaggle Credit Card CSV data (Time, V1..V28, Amount, Class) into the unified risk schema.
"""

from typing import Optional
import numpy as np
import pandas as pd

from src.adapters.base import BaseDatasetAdapter


class KaggleCreditCardAdapter(BaseDatasetAdapter):
    """
    Adapter for the Kaggle Credit Card Fraud Detection benchmark.
    Standardizes Time, Amount, Class, and PCA vectors into unified risk schema.
    """

    def __init__(self, start_date: str = "2018-04-01", n_customers: int = 50, n_terminals: int = 100):
        self.start_date = start_date
        self.n_customers = n_customers
        self.n_terminals = n_terminals

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw Kaggle DataFrame into standardized pipeline format.
        """
        required = ["Time", "Amount", "Class"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise KeyError(f"Kaggle DataFrame missing required columns: {missing}")

        out = pd.DataFrame()
        out["TRANSACTION_ID"] = np.arange(len(df))
        
        # Temporal mapping
        time_sec = df["Time"].astype(int)
        out["TX_TIME_SECONDS"] = time_sec
        out["TX_TIME_DAYS"] = (time_sec // 86400).astype(int)
        
        start_ts = pd.Timestamp(self.start_date)
        out["TX_DATETIME"] = start_ts + pd.to_timedelta(time_sec, unit="s")

        # Entity proxies (map PCA signatures or cluster into customer/terminal IDs)
        if "V1" in df.columns and "V2" in df.columns:
            # Deterministic proxy assignment from continuous features
            cust_proxy = np.abs((df["V1"] * 1000 + df["V2"] * 500).fillna(0).astype(int)) % self.n_customers
            out["CUSTOMER_ID"] = cust_proxy
        else:
            out["CUSTOMER_ID"] = np.random.randint(0, self.n_customers, size=len(df))

        if "V3" in df.columns and "V4" in df.columns:
            term_proxy = np.abs((df["V3"] * 800 + df["V4"] * 400).fillna(0).astype(int)) % self.n_terminals
            out["TERMINAL_ID"] = term_proxy
        else:
            out["TERMINAL_ID"] = np.random.randint(0, self.n_terminals, size=len(df))

        out["TX_AMOUNT"] = df["Amount"].astype(float).clip(lower=0.01)
        out["TX_FRAUD"] = df["Class"].astype(int)
        out["TX_FRAUD_SCENARIO"] = out["TX_FRAUD"]

        # Sort chronologically
        out = out.sort_values("TX_DATETIME").reset_index(drop=True)
        out["TRANSACTION_ID"] = out.index

        self.validate(out)
        return out


def generate_sample_kaggle_data(n_samples: int = 200, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic synthetic sample of raw Kaggle Credit Card dataset for testing.
    """
    np.random.seed(random_state)
    time_vals = np.sort(np.random.randint(0, 172800, size=n_samples))  # 2 days of seconds
    
    data = {
        "Time": time_vals,
        "Amount": np.round(np.random.exponential(scale=65.0, size=n_samples) + 1.0, 2),
        "Class": np.random.choice([0, 1], size=n_samples, p=[0.92, 0.08]),
    }
    for i in range(1, 29):
        data[f"V{i}"] = np.random.normal(0, 1, size=n_samples)

    return pd.DataFrame(data)
