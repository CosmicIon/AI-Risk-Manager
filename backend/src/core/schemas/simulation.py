"""Pydantic schemas for Fraud Detection Handbook simulation engine."""

from datetime import datetime

from pydantic import BaseModel, Field


class SimulationConfig(BaseModel):
    """Request body for dataset generation."""

    n_customers: int = Field(5000, ge=100, le=20000, description="Number of customer profiles")
    n_terminals: int = Field(500, ge=50, le=2000, description="Number of terminal profiles")
    nb_days: int = Field(90, ge=7, le=180, description="Simulation timespan in days")
    radius: float = Field(5.0, ge=1.0, le=15.0, description="Spatial association radius")
    seed: int = Field(42, description="Random seed for reproducibility")
    scenario_1_enabled: bool = Field(True, description="Enable Scenario 1 — High-Amount Fraud")
    scenario_2_enabled: bool = Field(True, description="Enable Scenario 2 — Compromised Terminals")
    scenario_3_enabled: bool = Field(True, description="Enable Scenario 3 — Account Takeover")
    high_amount_threshold: float = Field(
        22000.0, ge=5000.0, description="Scenario 1 amount threshold (₹)"
    )
    n_compromised_terminals_per_day: int = Field(
        2, ge=0, le=10, description="Scenario 2 — terminals compromised per day"
    )
    n_compromised_customers_per_day: int = Field(
        3, ge=0, le=10, description="Scenario 3 — customers compromised per day"
    )
    inr_multiplier: float = Field(1.0, ge=0.1, le=10.0, description="INR amount scaling factor")


class ScenarioBreakdown(BaseModel):
    """Fraud count breakdown per scenario."""

    scenario_0_legitimate: int = 0
    scenario_1_high_amount: int = 0
    scenario_2_compromised_terminal: int = 0
    scenario_3_account_takeover: int = 0


class SimulationStats(BaseModel):
    """Response body with dataset summary statistics."""

    total_transactions: int
    total_customers: int
    total_terminals: int
    nb_days: int
    fraud_count: int
    fraud_rate: float
    scenario_breakdown: ScenarioBreakdown
    total_loss_inr: float
    train_count: int
    holdout_count: int
    avg_amount: float
    median_amount: float
    generated_at: datetime

    # Coordinate data for spatial visualization
    customer_coordinates: list[dict] | None = Field(
        None, description="List of {x, y, customer_id} dicts"
    )
    terminal_coordinates: list[dict] | None = Field(
        None, description="List of {x, y, terminal_id, mcc} dicts"
    )
    compromised_terminals: list[str] | None = Field(
        None, description="Terminal IDs currently compromised (Scenario 2)"
    )
    compromised_customers: list[str] | None = Field(
        None, description="Customer IDs currently compromised (Scenario 3)"
    )


class StreamConfig(BaseModel):
    """Configuration for live transaction streaming."""

    tps_rate: int = Field(10, ge=1, le=100, description="Transactions per second")
    include_fraud_labels: bool = Field(True, description="Include ground truth in stream")


class SimulatedTransaction(BaseModel):
    """Individual transaction payload for WebSocket streaming."""

    transaction_id: str
    tx_datetime: str
    customer_id: str
    terminal_id: str
    tx_amount: float
    mcc: str
    payment_method: str
    device_fingerprint: str
    ip_address: str
    tx_fraud: int
    tx_fraud_scenario: int
    ml_risk_score: float = Field(0.0, description="Simulated ML model risk score")
