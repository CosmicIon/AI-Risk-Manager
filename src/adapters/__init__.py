"""
Dataset Adapters Package
Provides schema adapters for public fraud detection benchmarks (Kaggle Credit Card, IEEE-CIS).
"""

from src.adapters.base import BaseDatasetAdapter
from src.adapters.kaggle import KaggleCreditCardAdapter
from src.adapters.ieee_cis import IEEECISAdapter

__all__ = ["BaseDatasetAdapter", "KaggleCreditCardAdapter", "IEEECISAdapter"]
