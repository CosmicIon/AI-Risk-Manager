"""Generate Handbook-compliant synthetic data for AI Risk Manager.

This script uses the Fraud Detection Handbook simulation engine to produce
spatially-associated transactions with 3 canonical fraud scenarios, then
generates compatible returns and chargebacks datasets for downstream ML
training and evaluation pipelines.

Usage:
    cd backend
    python scripts/generate_synthetic_data.py
    python scripts/generate_synthetic_data.py --customers 10000 --terminals 1000 --days 120
"""

import argparse
import os
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src.core.schemas.simulation import SimulationConfig
from src.ml.simulation.generator import generate_complete_dataset


def generate_returns(txns: pd.DataFrame, num_returns: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Generate return requests from existing transactions.

    Preserves the existing returns schema for backward compatibility
    with run_evaluation.py and the returns ML pipeline.

    Args:
        txns: Transactions DataFrame.
        num_returns: Number of return requests to generate.
        seed: Random seed.

    Returns:
        Returns DataFrame.
    """
    rng = np.random.default_rng(seed)
    num_returns = min(num_returns, len(txns))

    return_txns = txns.sample(num_returns, replace=False, random_state=seed)
    abuse_count = int(num_returns * 0.05)
    abuse_indices = rng.choice(return_txns.index, size=abuse_count, replace=False)

    is_abusive = np.zeros(num_returns, dtype=bool)
    is_abusive[np.isin(return_txns.index, abuse_indices)] = True

    return_amounts = return_txns["tx_amount"].values * np.where(
        is_abusive, 1.0, rng.uniform(0.1, 1.0, num_returns)
    )
    return_amounts = np.round(return_amounts, 2)

    # Map MCC to category for backward compatibility
    mcc_to_category = {
        "5411": "groceries",
        "5732": "electronics",
        "5651": "fashion",
        "5812": "other",
        "4829": "other",
    }
    categories = return_txns["mcc"].map(mcc_to_category).fillna("other").values

    device_fingerprints = return_txns["device_fingerprint"].values.copy()
    for i in range(num_returns):
        if is_abusive[i] and rng.random() < 0.8:
            device_fingerprints[i] = f"device_mismatch_{rng.integers(1, 1000)}"

    returns = pd.DataFrame(
        {
            "request_id": [f"ret_{i:06d}" for i in range(num_returns)],
            "transaction_id": return_txns["transaction_id"].values,
            "customer_id": return_txns["customer_id"].values,
            "order_amount": return_txns["tx_amount"].values,
            "return_amount": return_amounts,
            "category": categories,
            "order_date": return_txns["tx_datetime"].values,
            "return_date": return_txns["tx_datetime"].values
            + pd.to_timedelta(rng.integers(1, 30, num_returns), unit="D"),
            "device_fingerprint": device_fingerprints,
            "is_abusive": is_abusive,
        }
    )

    returns = returns.sort_values("return_date").reset_index(drop=True)
    return returns


def generate_chargebacks(
    txns: pd.DataFrame, returns: pd.DataFrame, num_chargebacks: int = 500, seed: int = 42
) -> pd.DataFrame:
    """Generate chargeback cases from transactions not in returns.

    Args:
        txns: Transactions DataFrame.
        returns: Returns DataFrame (to exclude those transactions).
        num_chargebacks: Number of chargeback cases.
        seed: Random seed.

    Returns:
        Chargebacks DataFrame.
    """
    rng = np.random.default_rng(seed)

    eligible = txns[~txns["transaction_id"].isin(returns["transaction_id"])]
    num_chargebacks = min(num_chargebacks, len(eligible))
    cb_txns = eligible.sample(num_chargebacks, replace=False, random_state=seed)

    outcomes = rng.choice(["WON", "LOST", "PENDING"], num_chargebacks, p=[0.4, 0.5, 0.1])
    reason_codes = rng.choice(["10.4", "13.1", "13.3", "12.2"], num_chargebacks)

    chargebacks = pd.DataFrame(
        {
            "case_id": [f"cb_{i:06d}" for i in range(num_chargebacks)],
            "transaction_id": cb_txns["transaction_id"].values,
            "amount": cb_txns["tx_amount"].values,
            "reason_code": reason_codes,
            "outcome": outcomes,
            "created_at": cb_txns["tx_datetime"].values
            + pd.to_timedelta(rng.integers(10, 60, num_chargebacks), unit="D"),
        }
    )

    chargebacks = chargebacks.sort_values("created_at").reset_index(drop=True)
    return chargebacks


def split_and_save(df: pd.DataFrame, time_col: str, name: str, output_dir: str) -> None:
    """Split DataFrame 80/20 by time and save as Parquet."""
    holdout_dir = os.path.join(output_dir, "holdout")
    os.makedirs(holdout_dir, exist_ok=True)

    split_idx = int(len(df) * 0.8)
    train = df.iloc[:split_idx]
    holdout = df.iloc[split_idx:]

    train.to_parquet(os.path.join(output_dir, f"{name}.parquet"), index=False)
    holdout.to_parquet(os.path.join(holdout_dir, f"{name}.parquet"), index=False)
    print(f"  Saved {name}: Train {len(train):,}, Holdout {len(holdout):,}")


def generate_data(
    n_customers: int = 5000,
    n_terminals: int = 500,
    nb_days: int = 90,
    seed: int = 42,
) -> None:
    """Generate complete Handbook-compliant synthetic datasets.

    Produces:
      - transactions.parquet (with fraud scenarios)
      - returns.parquet
      - chargebacks.parquet
      - customers.parquet
      - terminals.parquet
    Each with train/holdout splits.
    """
    output_dir = os.path.join(str(backend_dir), "data", "synthetic")
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 58)
    print("  Fraud Detection Handbook - Synthetic Data Generator")
    print("=" * 58)
    print(f"  Customers: {n_customers:,}  |  Terminals: {n_terminals:,}  |  Days: {nb_days}")
    print()

    # 1. Generate Handbook-compliant transactions with fraud scenarios
    config = SimulationConfig(
        n_customers=n_customers,
        n_terminals=n_terminals,
        nb_days=nb_days,
        seed=seed,
    )

    print("[1] Generating customer & terminal profiles...")
    tx_df, customers_df, terminals_df = generate_complete_dataset(config)

    total_fraud = (tx_df["tx_fraud"] == 1).sum()
    fraud_rate = 100.0 * total_fraud / max(1, len(tx_df))
    print(f"  Generated {len(tx_df):,} transactions ({total_fraud:,} fraudulent, {fraud_rate:.2f}%)")

    # Save profiles
    customers_df.to_parquet(os.path.join(output_dir, "customers.parquet"), index=False)
    terminals_df.to_parquet(os.path.join(output_dir, "terminals.parquet"), index=False)
    print(f"  Saved {len(customers_df):,} customer profiles, {len(terminals_df):,} terminal profiles")

    # 2. Generate returns
    num_returns = min(5000, len(tx_df) // 20)
    print(f"\n[2] Generating {num_returns:,} return requests...")
    returns = generate_returns(tx_df, num_returns=num_returns, seed=seed)
    abuse_count = returns["is_abusive"].sum()
    print(f"  Generated {len(returns):,} returns ({abuse_count} abusive, {100*abuse_count/len(returns):.1f}%)")

    # 3. Generate chargebacks
    num_chargebacks = min(500, len(tx_df) // 200)
    print(f"\n[3] Generating {num_chargebacks:,} chargeback cases...")
    chargebacks = generate_chargebacks(tx_df, returns, num_chargebacks=num_chargebacks, seed=seed)
    print(f"  Generated {len(chargebacks):,} chargebacks")

    # 4. Save with train/holdout splits
    print(f"\n[4] Saving datasets with 80/20 time-split...")
    split_and_save(tx_df, "tx_datetime", "transactions", output_dir)
    split_and_save(returns, "return_date", "returns", output_dir)
    split_and_save(chargebacks, "created_at", "chargebacks", output_dir)

    # Summary
    s1 = (tx_df["tx_fraud_scenario"] == 1).sum()
    s2 = (tx_df["tx_fraud_scenario"] == 2).sum()
    s3 = (tx_df["tx_fraud_scenario"] == 3).sum()
    total_loss = tx_df.loc[tx_df["tx_fraud"] == 1, "tx_amount"].sum()

    print(f"\n{'=' * 58}")
    print(f"  [OK] Dataset generation complete!")
    print(f"  [OK] Output: {output_dir}")
    print(f"  [OK] Scenario 1 (High Amount):    {s1:>6,} transactions")
    print(f"  [OK] Scenario 2 (POS Skimming):   {s2:>6,} transactions")
    print(f"  [OK] Scenario 3 (Account Takeover):{s3:>5,} transactions")
    print(f"  [OK] Total INR loss:              INR {total_loss:>12,.2f}")
    print(f"{'=' * 58}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Handbook-compliant synthetic data for AI Risk Manager"
    )
    parser.add_argument("--customers", type=int, default=5000, help="Number of customers (default: 5000)")
    parser.add_argument("--terminals", type=int, default=500, help="Number of terminals (default: 500)")
    parser.add_argument("--days", type=int, default=90, help="Number of days (default: 90)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")

    args = parser.parse_args()
    generate_data(
        n_customers=args.customers,
        n_terminals=args.terminals,
        nb_days=args.days,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
