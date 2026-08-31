"""
Fraud Detection Handbook — Vectorized Transaction & Fraud Simulation Engine.

Faithfully implements the algorithms from:
  https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html

Adapted to Indian BFSI context (₹ amounts, MCC codes, UPI/CREDIT_CARD/DEBIT_CARD/NET_BANKING).

Mathematical Models
-------------------
- Customer profiles: (x,y) ~ U(0,100)², mean_amount ~ U(100,5000) ₹, std = mean/2,
  frequency ~ U(0.5, 4.0) tx/day
- Terminal profiles: (x,y) ~ U(0,100)², MCC weighted from {5411,5732,5651,5812,4829}
- Spatial association: Euclidean distance ≤ radius r, fallback to nearest terminal
- Transaction generation: Poisson(λ=frequency) daily count, N(mean, std²) amounts clipped ≥ ₹10,
  diurnal bias 10:00–22:00 IST
- Scenario 1: Amount > threshold → fraud
- Scenario 2: Compromised terminals → 100% fraud for 14 days
- Scenario 3: Compromised customers → 33% flagged, amount × 5 for 14 days
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from src.core.schemas.simulation import SimulationConfig

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

MCC_CODES = ["5411", "5732", "5651", "5812", "4829"]
MCC_WEIGHTS = [0.30, 0.15, 0.15, 0.25, 0.15]  # Grocery, Electronics, Apparel, Dining, Transfer

PAYMENT_METHODS = ["UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING"]
PAYMENT_WEIGHTS = [0.40, 0.25, 0.25, 0.10]

COMPROMISE_WINDOW_DAYS = 14
SCENARIO_3_FRACTION = 1 / 3


# ── Profile Generation ──────────────────────────────────────────────────────


def generate_customer_profiles_table(n_customers: int, seed: int = 42) -> pd.DataFrame:
    """Generate customer profiles with spatial coordinates and spending patterns.

    Each customer gets:
      - (x, y) ~ U(0, 100)²
      - mean_amount ~ U(100, 5000) ₹
      - std_amount = mean_amount / 2
      - mean_nb_tx_per_day ~ U(0.5, 4.0)

    Args:
        n_customers: Number of customers to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: customer_id, x_customer, y_customer,
        mean_amount, std_amount, mean_nb_tx_per_day.
    """
    rng = np.random.default_rng(seed)

    customer_ids = [f"C_{i:05d}" for i in range(n_customers)]
    x = rng.uniform(0, 100, n_customers)
    y = rng.uniform(0, 100, n_customers)
    mean_amount = rng.uniform(100, 5000, n_customers)
    std_amount = mean_amount / 2
    mean_nb_tx_per_day = rng.uniform(0.5, 4.0, n_customers)

    return pd.DataFrame(
        {
            "customer_id": customer_ids,
            "x_customer": x,
            "y_customer": y,
            "mean_amount": mean_amount,
            "std_amount": std_amount,
            "mean_nb_tx_per_day": mean_nb_tx_per_day,
        }
    )


def generate_terminal_profiles_table(n_terminals: int, seed: int = 42) -> pd.DataFrame:
    """Generate terminal profiles with spatial coordinates and MCC codes.

    Each terminal gets:
      - (x, y) ~ U(0, 100)²
      - MCC sampled with weighted probabilities across 5 categories

    Args:
        n_terminals: Number of terminals to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: terminal_id, x_terminal, y_terminal, mcc.
    """
    rng = np.random.default_rng(seed)

    terminal_ids = [f"T_{i:04d}" for i in range(n_terminals)]
    x = rng.uniform(0, 100, n_terminals)
    y = rng.uniform(0, 100, n_terminals)
    mcc = rng.choice(MCC_CODES, size=n_terminals, p=MCC_WEIGHTS)

    return pd.DataFrame(
        {
            "terminal_id": terminal_ids,
            "x_terminal": x,
            "y_terminal": y,
            "mcc": mcc,
        }
    )


# ── Spatial Association ─────────────────────────────────────────────────────


def map_customers_to_terminals(
    customers_df: pd.DataFrame,
    terminals_df: pd.DataFrame,
    radius: float = 5.0,
) -> dict[str, list[str]]:
    """Map each customer to terminals within Euclidean distance ≤ radius.

    Uses scipy.spatial.cKDTree for O(N log N) spatial queries instead of
    brute-force O(N²). If no terminal falls within the radius for a customer,
    assigns the single nearest terminal.

    Args:
        customers_df: Customer profiles with x_customer, y_customer columns.
        terminals_df: Terminal profiles with x_terminal, y_terminal columns.
        radius: Maximum Euclidean distance for association.

    Returns:
        Dict mapping customer_id → list of terminal_ids.
    """
    terminal_coords = terminals_df[["x_terminal", "y_terminal"]].values
    customer_coords = customers_df[["x_customer", "y_customer"]].values

    tree = cKDTree(terminal_coords)

    # Query all terminals within radius for each customer
    nearby_indices = tree.query_ball_point(customer_coords, r=radius)

    # For customers with no terminals in radius, find nearest one
    _, nearest_indices = tree.query(customer_coords, k=1)

    terminal_ids = terminals_df["terminal_id"].values
    customer_ids = customers_df["customer_id"].values

    mapping: dict[str, list[str]] = {}
    for i, cust_id in enumerate(customer_ids):
        indices = nearby_indices[i]
        if len(indices) == 0:
            indices = [int(nearest_indices[i])]
        mapping[cust_id] = [terminal_ids[j] for j in indices]

    return mapping


# ── Transaction Generation ──────────────────────────────────────────────────


def _generate_device_fingerprint(customer_id: str, tx_index: int) -> str:
    """Generate a deterministic device fingerprint per customer."""
    raw = f"{customer_id}_device_{tx_index % 3}"
    return f"dev_{hashlib.md5(raw.encode()).hexdigest()[:12]}"


def _generate_ip_address(rng: np.random.Generator) -> str:
    """Generate a random private IP address."""
    return f"10.{rng.integers(0, 256)}.{rng.integers(0, 256)}.{rng.integers(1, 255)}"


def generate_transactions_table(
    customers_df: pd.DataFrame,
    terminals_df: pd.DataFrame,
    customer_terminals: dict[str, list[str]],
    start_date: datetime,
    nb_days: int,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate transactions following the Handbook specification.

    For each customer across D days:
      1. Draw daily count K ~ Poisson(mean_nb_tx_per_day)
      2. For each transaction:
         - Time: sample seconds in [0, 86400) with diurnal bias (peak 10:00–22:00 IST)
         - Amount: N(mean_amount, std_amount²), clipped ≥ ₹10
         - Terminal: uniform random from customer's associated terminal list
         - Device/IP/Payment: assigned per customer with randomization

    Args:
        customers_df: Customer profiles DataFrame.
        terminals_df: Terminal profiles DataFrame (used for MCC lookup).
        customer_terminals: Mapping from customer_id to list of terminal_ids.
        start_date: Simulation start date.
        nb_days: Number of days to simulate.
        seed: Random seed.

    Returns:
        DataFrame with all transaction columns, sorted by tx_datetime.
    """
    rng = np.random.default_rng(seed)

    # Pre-compute terminal MCC lookup
    terminal_mcc = dict(zip(terminals_df["terminal_id"], terminals_df["mcc"]))

    all_records: list[dict] = []
    tx_counter = 0

    customer_data = customers_df.to_dict("records")

    for day_offset in range(nb_days):
        current_date = start_date + timedelta(days=day_offset)

        for cust in customer_data:
            cust_id = cust["customer_id"]
            mean_amount = cust["mean_amount"]
            std_amount = cust["std_amount"]
            mean_nb_tx = cust["mean_nb_tx_per_day"]

            # Poisson draw for daily transaction count
            n_tx = rng.poisson(mean_nb_tx)
            if n_tx == 0:
                continue

            # Available terminals for this customer
            available_terminals = customer_terminals.get(cust_id, [])
            if not available_terminals:
                continue

            for _ in range(n_tx):
                # Diurnal bias: 70% chance of peak hours (10:00–22:00 IST = 36000–79200 sec)
                if rng.random() < 0.7:
                    tx_time_seconds = int(rng.integers(36000, 79200))
                else:
                    tx_time_seconds = int(rng.integers(0, 86400))

                tx_datetime = current_date + timedelta(seconds=tx_time_seconds)

                # Amount: Normal distribution, clipped ≥ ₹10
                amount = float(max(10.0, rng.normal(mean_amount, std_amount)))
                amount = round(amount, 2)

                # Terminal: uniform random
                terminal_id = str(rng.choice(available_terminals))
                mcc = terminal_mcc.get(terminal_id, "5411")

                # Payment method
                payment_method = str(rng.choice(PAYMENT_METHODS, p=PAYMENT_WEIGHTS))

                # Device and IP
                device_fp = _generate_device_fingerprint(cust_id, tx_counter)
                ip_addr = _generate_ip_address(rng)

                all_records.append(
                    {
                        "transaction_id": f"TX_{tx_counter:08d}",
                        "tx_datetime": tx_datetime,
                        "customer_id": cust_id,
                        "terminal_id": terminal_id,
                        "tx_amount": amount,
                        "mcc": mcc,
                        "payment_method": payment_method,
                        "device_fingerprint": device_fp,
                        "ip_address": ip_addr,
                        "tx_time_seconds": tx_time_seconds,
                        "tx_time_days": day_offset,
                        "tx_fraud": 0,
                        "tx_fraud_scenario": 0,
                    }
                )
                tx_counter += 1

    tx_df = pd.DataFrame(all_records)

    if len(tx_df) > 0:
        tx_df = tx_df.sort_values("tx_datetime").reset_index(drop=True)
        # Re-assign sequential transaction IDs after sorting
        tx_df["transaction_id"] = [f"TX_{i:08d}" for i in range(len(tx_df))]

    logger.info(
        "Generated %d transactions across %d days for %d customers",
        len(tx_df),
        nb_days,
        len(customers_df),
    )
    return tx_df


# ── Fraud Scenario Injection ────────────────────────────────────────────────


def inject_fraud_scenarios(
    tx_df: pd.DataFrame,
    n_compromised_terminals_per_day: int = 2,
    n_compromised_customers_per_day: int = 3,
    high_amount_threshold: float = 22000.0,
    scenario_1_enabled: bool = True,
    scenario_2_enabled: bool = True,
    scenario_3_enabled: bool = True,
    seed: int = 42,
) -> pd.DataFrame:
    """Apply the 3 canonical fraud scenarios from the Handbook.

    Scenario 1 — High-Amount Point Fraud:
      tx_amount > threshold → tx_fraud=1, tx_fraud_scenario=1

    Scenario 2 — Compromised Terminals (POS Skimming):
      Each day, k₁ terminals are compromised. For the next 14 days,
      ALL transactions on those terminals are flagged.
      tx_fraud=1, tx_fraud_scenario=2

    Scenario 3 — Compromised Customers (Account Takeover):
      Each day, k₂ customers are compromised. For the next 14 days,
      1/3 of their transactions are selected, amount multiplied by 5×.
      tx_fraud=1, tx_fraud_scenario=3

    Args:
        tx_df: Transactions DataFrame (must contain tx_fraud, tx_fraud_scenario columns).
        n_compromised_terminals_per_day: Scenario 2 parameter.
        n_compromised_customers_per_day: Scenario 3 parameter.
        high_amount_threshold: Scenario 1 threshold in ₹.
        scenario_1_enabled: Toggle Scenario 1.
        scenario_2_enabled: Toggle Scenario 2.
        scenario_3_enabled: Toggle Scenario 3.
        seed: Random seed.

    Returns:
        DataFrame with tx_fraud and tx_fraud_scenario columns updated.
    """
    if tx_df.empty:
        return tx_df

    rng = np.random.default_rng(seed + 1000)  # Offset seed from generation
    df = tx_df.copy()

    # Ensure columns exist
    df["tx_fraud"] = 0
    df["tx_fraud_scenario"] = 0

    # ── Scenario 1: High-Amount Fraud ────────────────────────────────────
    if scenario_1_enabled:
        mask_s1 = df["tx_amount"] > high_amount_threshold
        df.loc[mask_s1, "tx_fraud"] = 1
        df.loc[mask_s1, "tx_fraud_scenario"] = 1
        n_s1 = mask_s1.sum()
        logger.info("Scenario 1: Flagged %d high-amount transactions (> ₹%.0f)", n_s1, high_amount_threshold)

    # ── Scenario 2: Compromised Terminals ────────────────────────────────
    if scenario_2_enabled and n_compromised_terminals_per_day > 0:
        unique_terminals = df["terminal_id"].unique()
        unique_days = sorted(df["tx_time_days"].unique())

        compromised_terminal_windows: list[tuple[str, int, int]] = []

        for day in unique_days:
            n_to_select = min(n_compromised_terminals_per_day, len(unique_terminals))
            selected = rng.choice(unique_terminals, size=n_to_select, replace=False)
            for tid in selected:
                compromised_terminal_windows.append(
                    (str(tid), int(day), int(day) + COMPROMISE_WINDOW_DAYS)
                )

        n_s2 = 0
        for terminal_id, start_day, end_day in compromised_terminal_windows:
            mask = (
                (df["terminal_id"] == terminal_id)
                & (df["tx_time_days"] >= start_day)
                & (df["tx_time_days"] < end_day)
                & (df["tx_fraud"] == 0)  # Don't override Scenario 1
            )
            df.loc[mask, "tx_fraud"] = 1
            df.loc[mask, "tx_fraud_scenario"] = 2
            n_s2 += mask.sum()

        logger.info(
            "Scenario 2: Flagged %d transactions on %d compromised terminal windows",
            n_s2,
            len(compromised_terminal_windows),
        )

    # ── Scenario 3: Compromised Customers ────────────────────────────────
    if scenario_3_enabled and n_compromised_customers_per_day > 0:
        unique_customers = df["customer_id"].unique()
        unique_days = sorted(df["tx_time_days"].unique())

        compromised_customer_windows: list[tuple[str, int, int]] = []

        for day in unique_days:
            n_to_select = min(n_compromised_customers_per_day, len(unique_customers))
            selected = rng.choice(unique_customers, size=n_to_select, replace=False)
            for cid in selected:
                compromised_customer_windows.append(
                    (str(cid), int(day), int(day) + COMPROMISE_WINDOW_DAYS)
                )

        n_s3 = 0
        for customer_id, start_day, end_day in compromised_customer_windows:
            mask_eligible = (
                (df["customer_id"] == customer_id)
                & (df["tx_time_days"] >= start_day)
                & (df["tx_time_days"] < end_day)
                & (df["tx_fraud"] == 0)  # Don't override earlier scenarios
            )
            eligible_indices = df.index[mask_eligible].tolist()

            if not eligible_indices:
                continue

            # Select ~1/3 of transactions
            n_to_flag = max(1, int(len(eligible_indices) * SCENARIO_3_FRACTION))
            flagged_indices = rng.choice(eligible_indices, size=n_to_flag, replace=False)

            df.loc[flagged_indices, "tx_fraud"] = 1
            df.loc[flagged_indices, "tx_fraud_scenario"] = 3
            # Multiply amount by 5×
            df.loc[flagged_indices, "tx_amount"] = df.loc[flagged_indices, "tx_amount"] * 5.0

            n_s3 += len(flagged_indices)

        logger.info(
            "Scenario 3: Flagged %d transactions for %d compromised customer windows",
            n_s3,
            len(compromised_customer_windows),
        )

    total_fraud = (df["tx_fraud"] == 1).sum()
    total_legit = (df["tx_fraud"] == 0).sum()
    logger.info(
        "Fraud injection complete: %d fraudulent / %d legitimate (%.2f%% fraud rate)",
        total_fraud,
        total_legit,
        100.0 * total_fraud / max(1, len(df)),
    )

    return df


# ── Orchestrator ─────────────────────────────────────────────────────────────


def generate_complete_dataset(
    config: SimulationConfig,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Generate a complete Handbook-compliant simulated dataset.

    Orchestrates profile generation, spatial association, transaction generation,
    and fraud scenario injection.

    Args:
        config: SimulationConfig with all parameters.

    Returns:
        Tuple of (transactions_df, customers_df, terminals_df).
    """
    logger.info(
        "Starting dataset generation: %d customers, %d terminals, %d days, radius=%.1f",
        config.n_customers,
        config.n_terminals,
        config.nb_days,
        config.radius,
    )

    # 1. Generate profiles
    customers_df = generate_customer_profiles_table(config.n_customers, seed=config.seed)
    terminals_df = generate_terminal_profiles_table(config.n_terminals, seed=config.seed + 1)

    # 2. Spatial association
    customer_terminals = map_customers_to_terminals(customers_df, terminals_df, radius=config.radius)
    logger.info(
        "Spatial association complete: avg %.1f terminals per customer",
        np.mean([len(v) for v in customer_terminals.values()]),
    )

    # 3. Generate transactions
    start_date = datetime(2025, 1, 1)
    tx_df = generate_transactions_table(
        customers_df,
        terminals_df,
        customer_terminals,
        start_date=start_date,
        nb_days=config.nb_days,
        seed=config.seed + 2,
    )

    # 4. Apply INR multiplier
    if config.inr_multiplier != 1.0:
        tx_df["tx_amount"] = (tx_df["tx_amount"] * config.inr_multiplier).round(2)

    # 5. Inject fraud scenarios
    tx_df = inject_fraud_scenarios(
        tx_df,
        n_compromised_terminals_per_day=config.n_compromised_terminals_per_day,
        n_compromised_customers_per_day=config.n_compromised_customers_per_day,
        high_amount_threshold=config.high_amount_threshold,
        scenario_1_enabled=config.scenario_1_enabled,
        scenario_2_enabled=config.scenario_2_enabled,
        scenario_3_enabled=config.scenario_3_enabled,
        seed=config.seed,
    )

    logger.info(
        "Dataset generation complete: %d transactions, %.2f%% fraud rate",
        len(tx_df),
        100.0 * (tx_df["tx_fraud"] == 1).sum() / max(1, len(tx_df)),
    )

    return tx_df, customers_df, terminals_df
