"""
Module: IEEE-CIS Fraud Detection Benchmark Adapter
Converts raw IEEE-CIS tabular transaction records into the unified risk schema.
"""

import numpy as np
import pandas as pd

from src.adapters.base import BaseDatasetAdapter


class IEEECISAdapter(BaseDatasetAdapter):
    """
    Adapter for the IEEE-CIS Fraud Detection Benchmark dataset.
    Maps TransactionID, TransactionDT, TransactionAmt, isFraud, card1, and addr1.
    """

    def __init__(self, start_date: str = "2018-04-01", n_customers: int = 50, n_terminals: int = 100):
        self.start_date = start_date
        self.n_customers = n_customers
        self.n_terminals = n_terminals

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw IEEE-CIS DataFrame into standardized pipeline format.
        """
        required = ["TransactionID", "TransactionDT", "TransactionAmt", "isFraud"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise KeyError(f"IEEE-CIS DataFrame missing required columns: {missing}")

        out = pd.DataFrame()
        out["TRANSACTION_ID"] = df["TransactionID"].astype(int)

        # Time mapping
        dt_seconds = df["TransactionDT"].astype(int)
        out["TX_TIME_SECONDS"] = dt_seconds
        out["TX_TIME_DAYS"] = (dt_seconds // 86400).astype(int)

        start_ts = pd.Timestamp(self.start_date)
        out["TX_DATETIME"] = start_ts + pd.to_timedelta(dt_seconds, unit="s")

        # Entity proxies
        if "card1" in df.columns:
            out["CUSTOMER_ID"] = (df["card1"].fillna(0).astype(int) % self.n_customers).astype(int)
        else:
            out["CUSTOMER_ID"] = np.random.randint(0, self.n_customers, size=len(df))

        if "addr1" in df.columns:
            out["TERMINAL_ID"] = (df["addr1"].fillna(0).astype(int) % self.n_terminals).astype(int)
        else:
            out["TERMINAL_ID"] = np.random.randint(0, self.n_terminals, size=len(df))

        out["TX_AMOUNT"] = df["TransactionAmt"].astype(float).clip(lower=0.01)
        out["TX_FRAUD"] = df["isFraud"].astype(int)
        out["TX_FRAUD_SCENARIO"] = out["TX_FRAUD"]

        # Sort chronologically
        out = out.sort_values("TX_DATETIME").reset_index(drop=True)
        out["TRANSACTION_ID"] = out.index

        self.validate(out)
        return out


def generate_sample_ieee_cis_data(n_samples: int = 200, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a realistic synthetic sample of raw IEEE-CIS dataset for testing.
    """
    np.random.seed(random_state)
    time_vals = np.sort(np.random.randint(86400, 86400 * 30, size=n_samples))

    data = {
        "TransactionID": np.arange(3000000, 3000000 + n_samples),
        "TransactionDT": time_vals,
        "TransactionAmt": np.round(np.random.exponential(scale=110.0, size=n_samples) + 5.0, 2),
        "isFraud": np.random.choice([0, 1], size=n_samples, p=[0.95, 0.05]),
        "card1": np.random.randint(1000, 18000, size=n_samples),
        "addr1": np.random.randint(100, 500, size=n_samples),
    }

    return pd.DataFrame(data)
