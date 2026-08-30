"""Fraud Detection Handbook — Transaction & Fraud Simulation Engine."""

from src.ml.simulation.generator import (
    generate_complete_dataset,
    generate_customer_profiles_table,
    generate_terminal_profiles_table,
    generate_transactions_table,
    inject_fraud_scenarios,
    map_customers_to_terminals,
)

__all__ = [
    "generate_customer_profiles_table",
    "generate_terminal_profiles_table",
    "map_customers_to_terminals",
    "generate_transactions_table",
    "inject_fraud_scenarios",
    "generate_complete_dataset",
]
