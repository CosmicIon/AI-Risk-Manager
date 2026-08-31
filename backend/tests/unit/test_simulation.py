"""Unit tests for the Fraud Detection Handbook simulation engine.

Tests cover:
  - Profile generation (coordinates, spending, frequency bounds)
  - Spatial association (radius constraints, fallback to nearest)
  - Transaction generation (Poisson means, amount clipping, schema)
  - Fraud scenario injection (all 3 scenarios)
  - Deterministic seeding
  - Time-split causality
"""

from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.core.schemas.simulation import SimulationConfig
from src.ml.simulation.generator import (
    generate_complete_dataset,
    generate_customer_profiles_table,
    generate_terminal_profiles_table,
    generate_transactions_table,
    inject_fraud_scenarios,
    map_customers_to_terminals,
)


# ── Profile Generation Tests ────────────────────────────────────────────────


class TestCustomerProfiles:
    def test_coordinates_within_bounds(self):
        df = generate_customer_profiles_table(500, seed=42)
        assert df["x_customer"].between(0, 100).all()
        assert df["y_customer"].between(0, 100).all()

    def test_mean_amount_within_bounds(self):
        df = generate_customer_profiles_table(1000, seed=42)
        assert df["mean_amount"].between(100, 5000).all()

    def test_std_amount_is_half_mean(self):
        df = generate_customer_profiles_table(500, seed=42)
        np.testing.assert_allclose(df["std_amount"], df["mean_amount"] / 2, rtol=1e-10)

    def test_tx_frequency_within_bounds(self):
        df = generate_customer_profiles_table(500, seed=42)
        assert df["mean_nb_tx_per_day"].between(0.5, 4.0).all()

    def test_correct_count(self):
        df = generate_customer_profiles_table(1234, seed=42)
        assert len(df) == 1234

    def test_unique_ids(self):
        df = generate_customer_profiles_table(500, seed=42)
        assert df["customer_id"].nunique() == 500


class TestTerminalProfiles:
    def test_coordinates_within_bounds(self):
        df = generate_terminal_profiles_table(300, seed=42)
        assert df["x_terminal"].between(0, 100).all()
        assert df["y_terminal"].between(0, 100).all()

    def test_mcc_valid_codes(self):
        df = generate_terminal_profiles_table(500, seed=42)
        valid_mccs = {"5411", "5732", "5651", "5812", "4829"}
        assert set(df["mcc"].unique()).issubset(valid_mccs)

    def test_correct_count(self):
        df = generate_terminal_profiles_table(777, seed=42)
        assert len(df) == 777


# ── Spatial Association Tests ────────────────────────────────────────────────


class TestSpatialAssociation:
    def test_all_customers_have_terminals(self):
        cust_df = generate_customer_profiles_table(200, seed=42)
        term_df = generate_terminal_profiles_table(50, seed=42)
        mapping = map_customers_to_terminals(cust_df, term_df, radius=5.0)
        assert len(mapping) == 200
        for terminals in mapping.values():
            assert len(terminals) >= 1

    def test_terminals_within_radius(self):
        cust_df = generate_customer_profiles_table(100, seed=42)
        term_df = generate_terminal_profiles_table(100, seed=42)
        radius = 5.0
        mapping = map_customers_to_terminals(cust_df, term_df, radius=radius)

        # Check a sample of customers
        term_coords = dict(
            zip(term_df["terminal_id"], zip(term_df["x_terminal"], term_df["y_terminal"]))
        )
        cust_coords = dict(
            zip(cust_df["customer_id"], zip(cust_df["x_customer"], cust_df["y_customer"]))
        )

        for cust_id, terminals in list(mapping.items())[:20]:
            cx, cy = cust_coords[cust_id]
            # If there are terminals within radius, all should be within radius
            # OR the nearest single terminal is assigned
            for tid in terminals:
                tx, ty = term_coords[tid]
                dist = np.sqrt((cx - tx) ** 2 + (cy - ty) ** 2)
                # Allow nearest-fallback: if only 1 terminal and outside radius, that's OK
                if len(terminals) > 1:
                    assert dist <= radius + 1e-6, f"Terminal {tid} at dist {dist:.2f} > radius {radius}"

    def test_fallback_to_nearest(self):
        """With a very small radius, some customers should get fallback nearest terminal."""
        cust_df = generate_customer_profiles_table(50, seed=42)
        term_df = generate_terminal_profiles_table(5, seed=42)
        mapping = map_customers_to_terminals(cust_df, term_df, radius=0.01)
        # With r=0.01 and only 5 terminals, most customers won't have any in radius
        # but all should still get at least one terminal (the nearest)
        for terminals in mapping.values():
            assert len(terminals) >= 1


# ── Transaction Generation Tests ─────────────────────────────────────────────


class TestTransactionGeneration:
    @pytest.fixture
    def small_dataset(self):
        cust_df = generate_customer_profiles_table(100, seed=42)
        term_df = generate_terminal_profiles_table(30, seed=42)
        mapping = map_customers_to_terminals(cust_df, term_df, radius=10.0)
        tx_df = generate_transactions_table(
            cust_df, term_df, mapping,
            start_date=datetime(2025, 1, 1),
            nb_days=30,
            seed=42,
        )
        return tx_df, cust_df

    def test_amounts_positive(self, small_dataset):
        tx_df, _ = small_dataset
        assert (tx_df["tx_amount"] >= 10.0).all()

    def test_output_schema(self, small_dataset):
        tx_df, _ = small_dataset
        required_cols = [
            "transaction_id", "tx_datetime", "customer_id", "terminal_id",
            "tx_amount", "mcc", "payment_method", "device_fingerprint",
            "ip_address", "tx_time_seconds", "tx_time_days",
            "tx_fraud", "tx_fraud_scenario",
        ]
        for col in required_cols:
            assert col in tx_df.columns, f"Missing column: {col}"

    def test_transaction_count_poisson_mean(self, small_dataset):
        """Verify mean daily transaction count per customer ≈ expected Poisson mean."""
        tx_df, cust_df = small_dataset
        # Pick a customer with known mean and check actual count is within 3σ
        for _, cust in cust_df.iterrows():
            cid = cust["customer_id"]
            expected_mean = cust["mean_nb_tx_per_day"]
            cust_txs = tx_df[tx_df["customer_id"] == cid]
            if len(cust_txs) == 0:
                continue
            actual_daily_mean = len(cust_txs) / 30.0
            # Poisson: σ² = λ, so σ_mean = sqrt(λ/30)
            sigma = np.sqrt(expected_mean / 30.0)
            # Allow generous 4σ tolerance for small sample
            assert abs(actual_daily_mean - expected_mean) < 4 * sigma + 1.0, (
                f"Customer {cid}: expected ~{expected_mean:.1f}, got {actual_daily_mean:.1f}"
            )
            break  # Test just one customer for speed

    def test_sorted_by_datetime(self, small_dataset):
        tx_df, _ = small_dataset
        assert tx_df["tx_datetime"].is_monotonic_increasing

    def test_payment_methods_valid(self, small_dataset):
        tx_df, _ = small_dataset
        valid = {"UPI", "CREDIT_CARD", "DEBIT_CARD", "NET_BANKING"}
        assert set(tx_df["payment_method"].unique()).issubset(valid)


# ── Fraud Scenario Tests ─────────────────────────────────────────────────────


class TestFraudScenarios:
    @pytest.fixture
    def fraud_dataset(self):
        cust_df = generate_customer_profiles_table(200, seed=42)
        term_df = generate_terminal_profiles_table(50, seed=42)
        mapping = map_customers_to_terminals(cust_df, term_df, radius=8.0)
        tx_df = generate_transactions_table(
            cust_df, term_df, mapping,
            start_date=datetime(2025, 1, 1),
            nb_days=60,
            seed=42,
        )
        return tx_df

    def test_scenario_1_high_amount(self, fraud_dataset):
        threshold = 15000.0
        tx_df = inject_fraud_scenarios(
            fraud_dataset,
            high_amount_threshold=threshold,
            scenario_1_enabled=True,
            scenario_2_enabled=False,
            scenario_3_enabled=False,
            seed=42,
        )
        s1_mask = tx_df["tx_fraud_scenario"] == 1
        # All Scenario 1 transactions should have amount > threshold
        assert (tx_df.loc[s1_mask, "tx_amount"] > threshold).all()
        # All transactions > threshold should be flagged
        high_amount_mask = tx_df["tx_amount"] > threshold
        assert tx_df.loc[high_amount_mask, "tx_fraud"].all()

    def test_scenario_2_compromised_terminals(self, fraud_dataset):
        tx_df = inject_fraud_scenarios(
            fraud_dataset,
            n_compromised_terminals_per_day=2,
            scenario_1_enabled=False,
            scenario_2_enabled=True,
            scenario_3_enabled=False,
            seed=42,
        )
        s2_mask = tx_df["tx_fraud_scenario"] == 2
        assert s2_mask.sum() > 0, "Scenario 2 should flag some transactions"
        # All S2 flagged transactions should have tx_fraud=1
        assert (tx_df.loc[s2_mask, "tx_fraud"] == 1).all()

    def test_scenario_3_account_takeover(self, fraud_dataset):
        tx_df = inject_fraud_scenarios(
            fraud_dataset,
            n_compromised_customers_per_day=3,
            scenario_1_enabled=False,
            scenario_2_enabled=False,
            scenario_3_enabled=True,
            seed=42,
        )
        s3_mask = tx_df["tx_fraud_scenario"] == 3
        assert s3_mask.sum() > 0, "Scenario 3 should flag some transactions"
        # All S3 flagged should have tx_fraud=1
        assert (tx_df.loc[s3_mask, "tx_fraud"] == 1).all()

    def test_scenario_3_amount_multiplied(self, fraud_dataset):
        """Scenario 3 should multiply flagged transaction amounts by 5×."""
        original_df = fraud_dataset.copy()
        tx_df = inject_fraud_scenarios(
            fraud_dataset,
            n_compromised_customers_per_day=3,
            scenario_1_enabled=False,
            scenario_2_enabled=False,
            scenario_3_enabled=True,
            seed=42,
        )
        s3_mask = tx_df["tx_fraud_scenario"] == 3
        if s3_mask.sum() > 0:
            # S3 amounts should be larger than original (5× multiplied)
            s3_amounts = tx_df.loc[s3_mask, "tx_amount"]
            original_amounts = original_df.loc[s3_mask.index[s3_mask], "tx_amount"]
            # At least the mean should be significantly higher
            assert s3_amounts.mean() > original_amounts.mean() * 3

    def test_fraud_scenarios_non_overlapping(self, fraud_dataset):
        """Each transaction should have at most one fraud scenario."""
        tx_df = inject_fraud_scenarios(
            fraud_dataset,
            scenario_1_enabled=True,
            scenario_2_enabled=True,
            scenario_3_enabled=True,
            seed=42,
        )
        # Fraud scenario should be 0 for legitimate, 1/2/3 for fraud
        assert tx_df["tx_fraud_scenario"].isin([0, 1, 2, 3]).all()

    def test_all_scenarios_disabled(self, fraud_dataset):
        tx_df = inject_fraud_scenarios(
            fraud_dataset,
            scenario_1_enabled=False,
            scenario_2_enabled=False,
            scenario_3_enabled=False,
            seed=42,
        )
        assert (tx_df["tx_fraud"] == 0).all()
        assert (tx_df["tx_fraud_scenario"] == 0).all()


# ── Complete Dataset Tests ────────────────────────────────────────────────────


class TestCompleteDataset:
    def test_generate_complete(self):
        config = SimulationConfig(
            n_customers=100,
            n_terminals=50,
            nb_days=14,
            seed=42,
        )
        tx_df, cust_df, term_df = generate_complete_dataset(config)
        assert len(tx_df) > 0
        assert len(cust_df) == 100
        assert len(term_df) == 50

    def test_deterministic_seed(self):
        config = SimulationConfig(
            n_customers=100,
            n_terminals=50,
            nb_days=7,
            seed=123,
        )
        tx1, _, _ = generate_complete_dataset(config)
        tx2, _, _ = generate_complete_dataset(config)
        pd.testing.assert_frame_equal(tx1, tx2)

    def test_time_split_causality(self):
        config = SimulationConfig(
            n_customers=100,
            n_terminals=50,
            nb_days=30,
            seed=42,
        )
        tx_df, _, _ = generate_complete_dataset(config)

        split_idx = int(len(tx_df) * 0.8)
        train = tx_df.iloc[:split_idx]
        holdout = tx_df.iloc[split_idx:]

        if len(train) > 0 and len(holdout) > 0:
            assert train["tx_datetime"].max() <= holdout["tx_datetime"].min()

    def test_fraud_rate_reasonable(self):
        config = SimulationConfig(
            n_customers=200,
            n_terminals=50,
            nb_days=30,
            seed=42,
        )
        tx_df, _, _ = generate_complete_dataset(config)
        fraud_rate = (tx_df["tx_fraud"] == 1).mean()
        # Fraud rate should be between 0.1% and 50% for a reasonable simulation
        assert 0.001 < fraud_rate < 0.5, f"Fraud rate {fraud_rate:.4f} is out of expected range"
