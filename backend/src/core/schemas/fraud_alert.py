"""Fraud spike and anomaly detection alert schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from src.core.enums import AlertSeverity, SpikeClassification


class AnomalyAlert(BaseModel):
    """Alert generated when a streaming transaction spike is detected."""

    alert_id: UUID
    tenant_id: UUID
    detected_at: datetime
    severity: AlertSeverity
    spike_classification: SpikeClassification
    affected_segment: str
    baseline_tps: float
    current_tps: float
    deviation_factor: float
    window_seconds: int
    is_calendar_adjusted: bool


class FraudSpikeDetail(BaseModel):
    """Detailed analytics associated with a fraud spike alert."""

    alert_id: UUID
    transaction_ids: list[str]
    geographic_spread: dict[str, int]
    amount_distribution: dict[str, float]
    velocity_profile: list[dict[str, Any]]
