"""
Module: Base Dataset Adapter
Defines standard schema specifications and validation rules for external fraud datasets.
"""

from abc import ABC, abstractmethod
from typing import List
import pandas as pd


class BaseDatasetAdapter(ABC):
    """
    Abstract Base Class for adapting external fraud datasets into the unified
    AI-Risk-Manager pipeline schema.
    """

    REQUIRED_COLUMNS: List[str] = [
        "TRANSACTION_ID",
        "TX_DATETIME",
        "TX_TIME_DAYS",
        "TX_TIME_SECONDS",
        "CUSTOMER_ID",
        "TERMINAL_ID",
        "TX_AMOUNT",
        "TX_FRAUD",
    ]

    @abstractmethod
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw dataset DataFrame into standard pipeline format.
        """
        pass

    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validates that the standardized DataFrame satisfies all schema contracts.
        """
        # 1. Column presence
        missing = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise ValueError(f"Standardized DataFrame missing required columns: {missing}")

        # 2. Null values check
        null_counts = df[self.REQUIRED_COLUMNS].isnull().sum()
        if null_counts.any():
            bad_cols = null_counts[null_counts > 0].to_dict()
            raise ValueError(f"Null values detected in standardized columns: {bad_cols}")

        # 3. Label integrity
        fraud_vals = set(df["TX_FRAUD"].unique())
        if not fraud_vals.issubset({0, 1}):
            raise ValueError(f"TX_FRAUD contains invalid values: {fraud_vals}. Expected subset of {{0, 1}}.")

        # 4. Amount non-negative
        if (df["TX_AMOUNT"] < 0).any():
            raise ValueError("Negative transaction amounts found in standardized data.")

        return True
