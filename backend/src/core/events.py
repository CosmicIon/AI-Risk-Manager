"""Kafka event schemas wrapping domain models for streaming."""

from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from src.core.schemas.chargeback import ChargebackNotification
from src.core.schemas.fraud_alert import AnomalyAlert
from src.core.schemas.return_request import ReturnScoreRequest, ReturnScoreResponse


class TransactionEvent(BaseModel):
    """Raw transaction ingestion event flowing from Kafka."""

    event_id: str
    tenant_id: UUID
    transaction_id: str
    timestamp: datetime
    amount: Decimal
    currency: str
    merchant_id: str
    merchant_category_code: str
    customer_id: str
    payment_method: str
    device_fingerprint: str | None = None
    ip_address: str | None = None
    city: str | None = None
    country: str = "IN"


class ChargebackEvent(BaseModel):
    """Chargeback lifecycle event."""

    event_type: Literal[
        "chargeback.received",
        "chargeback.evidence_ready",
        "chargeback.submitted",
        "chargeback.resolved",
    ]
    payload: ChargebackNotification


class ReturnEvent(BaseModel):
    """Return scoring lifecycle event."""

    event_type: Literal["return.scored", "return.decision_overridden"]
    request: ReturnScoreRequest
    response: ReturnScoreResponse | None = None


class AlertEvent(BaseModel):
    """System or fraud alert event."""

    event_type: Literal["alert.fraud_spike", "alert.abuse_ring"]
    payload: AnomalyAlert


TOPIC_MAP: dict[str, type[BaseModel]] = {
    "transactions.raw": TransactionEvent,
    "chargebacks.incoming": ChargebackEvent,
    "returns.scored": ReturnEvent,
    "alerts.fraud": AlertEvent,
}
