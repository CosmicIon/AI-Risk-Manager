"""Chargeback data models and validation schemas."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, computed_field, model_validator

from src.core.enums import CardNetwork, CaseStatus, ReasonCode


class ChargebackNotification(BaseModel):
    """Raw chargeback notification received from a card network or acquirer."""
    notification_id: str
    network: CardNetwork
    arn: str
    raw_reason_code: str
    reason_code: ReasonCode
    transaction_id: str
    transaction_date: datetime
    transaction_amount: Decimal
    currency: str = "INR"
    cardholder_name: str | None = None
    merchant_id: str
    tenant_id: UUID
    received_at: datetime
    deadline: datetime | None = None

    @model_validator(mode="after")
    def compute_deadline(self) -> "ChargebackNotification":
        """Compute the response deadline based on the network if not provided."""
        if self.deadline is None:
            if self.network == CardNetwork.VISA:
                self.deadline = self.received_at + timedelta(days=30)
            elif self.network == CardNetwork.MASTERCARD:
                self.deadline = self.received_at + timedelta(days=45)
            else:
                self.deadline = self.received_at + timedelta(days=30)  # Default
        return self

    @computed_field
    def idempotency_key(self) -> str:
        """Deterministic key to prevent duplicate processing of the same dispute."""
        return f"{self.network.value}:{self.arn}"


class EvidenceItem(BaseModel):
    """A single piece of evidence gathered for a chargeback case."""
    evidence_type: Literal[
        "delivery_proof", 
        "avs_match", 
        "3ds_log", 
        "customer_communication", 
        "order_confirmation", 
        "refund_receipt", 
        "ip_geolocation"
    ]
    source: str
    content: str | None = None
    file_url: str | None = None
    retrieved_at: datetime
    confidence: float


class EvidenceBundle(BaseModel):
    """Collection of all evidence items associated with a case."""
    case_id: UUID
    items: list[EvidenceItem]
    completeness_score: float
    missing_evidence: list[str]


class RepresentmentDraft(BaseModel):
    """AI-generated representment package ready for human review."""
    case_id: UUID
    narrative: str
    evidence_summary: str
    network_template_version: str
    win_probability: float
    recommendation: Literal["respond", "accept_loss"]
    generated_at: datetime
    llm_model_used: str
    prompt_version: str


class ChargebackIngestRequest(BaseModel):
    """Request payload for ingesting a new chargeback webhook."""
    raw_payload: dict[str, Any]
    source_ip: str | None = None
    webhook_signature: str | None = None


class ChargebackIngestResponse(BaseModel):
    """Response returned upon successful chargeback ingestion."""
    case_id: UUID
    status: CaseStatus
    deadline: datetime
    message: str
