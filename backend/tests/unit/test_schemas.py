"""Unit tests for Pydantic and Avro schemas in AI Risk Manager."""

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import fastavro
import pytest
from pydantic import ValidationError

from src.core.enums import CardNetwork, ReasonCode, RiskTier
from src.core.schemas.chargeback import ChargebackNotification
from src.core.schemas.evaluation import CostWeightedMetrics
from src.core.schemas.return_request import ReturnScoreRequest, ReturnScoreResponse

# --- Chargeback Schemas ---

def test_chargeback_deadline_visa():
    """Visa chargebacks should auto-compute a 30-day deadline."""
    received = datetime.now(UTC)
    cb = ChargebackNotification(
        notification_id="cb-1",
        network=CardNetwork.VISA,
        arn="1234567890",
        raw_reason_code="10.4",
        reason_code=ReasonCode.FRAUD_CARD_NOT_PRESENT,
        transaction_id="tx-1",
        transaction_date=received - timedelta(days=5),
        transaction_amount=Decimal("1500.00"),
        merchant_id="merch-1",
        tenant_id=uuid4(),
        received_at=received
    )
    assert cb.deadline is not None
    assert cb.deadline == received + timedelta(days=30)
    assert cb.idempotency_key == "VISA:1234567890"

def test_chargeback_deadline_mastercard():
    """Mastercard chargebacks should auto-compute a 45-day deadline."""
    received = datetime.now(UTC)
    cb = ChargebackNotification(
        notification_id="cb-2",
        network=CardNetwork.MASTERCARD,
        arn="9876543210",
        raw_reason_code="4837",
        reason_code=ReasonCode.UNAUTHORIZED_TRANSACTION,
        transaction_id="tx-2",
        transaction_date=received - timedelta(days=5),
        transaction_amount=Decimal("2000.00"),
        merchant_id="merch-1",
        tenant_id=uuid4(),
        received_at=received
    )
    assert cb.deadline is not None
    assert cb.deadline == received + timedelta(days=45)
    assert cb.idempotency_key == "MASTERCARD:9876543210"


# --- Return Score Schemas ---

def test_return_score_request_valid():
    """Valid return score request."""
    req = ReturnScoreRequest(
        request_id="req-1",
        tenant_id=uuid4(),
        customer_id="cust-1",
        order_id="ord-1",
        order_amount=Decimal("5000.00"),
        return_amount=Decimal("2000.00"),
        return_reason="defective",
        order_date=datetime.now(UTC) - timedelta(days=2),
        return_initiated_at=datetime.now(UTC),
        product_category="electronics"
    )
    assert req.return_amount == Decimal("2000.00")

def test_return_score_request_invalid_amount():
    """Return amount > order amount should raise ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        ReturnScoreRequest(
            request_id="req-1",
            tenant_id=uuid4(),
            customer_id="cust-1",
            order_id="ord-1",
            order_amount=Decimal("1000.00"),
            return_amount=Decimal("2000.00"),  # > order_amount
            return_reason="defective",
            order_date=datetime.now(UTC),
            return_initiated_at=datetime.now(UTC),
            product_category="electronics"
        )
    assert "return_amount cannot exceed order_amount" in str(exc_info.value)

def test_return_score_response_clamps_score():
    """Risk score should be clamped between 0 and 100."""
    resp = ReturnScoreResponse(
        request_id="req-1",
        risk_score=150,  # Will be clamped to 100
        risk_tier=RiskTier.CRITICAL,
        decision="auto_deny",
        explanation="High velocity of returns",
        top_features=[],
        model_version="v1",
        inference_latency_ms=4.5,
        scored_at=datetime.now(UTC)
    )
    assert resp.risk_score == 100

    resp2 = ReturnScoreResponse(
        request_id="req-1",
        risk_score=-50,  # Will be clamped to 0
        risk_tier=RiskTier.LOW,
        decision="auto_approve",
        explanation="Trusted customer",
        top_features=[],
        model_version="v1",
        inference_latency_ms=2.1,
        scored_at=datetime.now(UTC)
    )
    assert resp2.risk_score == 0


# --- Evaluation Schemas ---

def test_cost_weighted_loss_computation():
    """Cost-weighted loss should be computed correctly based on FP/FN counts and costs."""
    metrics = CostWeightedMetrics(
        precision=0.8,
        recall=0.9,
        f1=0.85,
        auc_roc=0.92,
        tp_count=90,
        tn_count=800,
        fp_count=10,
        fn_count=100,
        fp_cost_per_unit=Decimal("500.00"), # E.g., blocking a good customer
        fn_cost_per_unit=Decimal("2000.00") # E.g., missing a fraudulent return
    )

    assert metrics.total_fp_cost == Decimal("5000.00")
    assert metrics.total_fn_cost == Decimal("200000.00")

    total_samples = 90 + 800 + 10 + 100
    expected_loss = (5000.0 + 200000.0) / total_samples
    assert metrics.cost_weighted_loss == pytest.approx(expected_loss)


# --- Enums ---

def test_enum_json_serialization():
    """Enums should serialize as their string values."""
    data = {"network": CardNetwork.VISA}
    # Pydantic's BaseModel.model_dump_json handles enums. We can test standard json with .value
    assert json.dumps({"network": data["network"].value}) == '{"network": "VISA"}'


# --- Avro Schemas Parsing ---

def test_avro_schemas_parseable():
    """Ensure Avro schema definitions in data/schemas/ are parseable by fastavro."""
    schemas_to_test = [
        "data/schemas/transaction.avsc",
        "data/schemas/chargeback_notification.avsc",
        "data/schemas/return_request.avsc"
    ]

    import os
    # __file__ is backend/tests/unit/test_schemas.py
    # Up 3 levels to reach the AI-Risk-Manager root
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    for schema_path in schemas_to_test:
        full_path = os.path.join(base_dir, schema_path)
        with open(full_path) as f:
            schema_dict = json.load(f)
            # fastavro.parse_schema raises an exception if invalid
            parsed_schema = fastavro.parse_schema(schema_dict)
            assert parsed_schema is not None
            assert parsed_schema["type"] == "record"
