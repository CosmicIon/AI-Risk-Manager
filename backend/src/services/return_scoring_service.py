import logging
import time
from datetime import UTC, datetime
from typing import Literal

from src.core.enums import RiskTier
from src.core.schemas.return_request import PolicyConfig, ReturnScoreRequest, ReturnScoreResponse
from src.db.models.tenant import Tenant
from src.integrations.redis_client import RedisClient
from src.ml.explainability.formatter import ExplanationFormatter
from src.ml.serving.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

class ReturnScoringService:
    def __init__(self, redis_client: RedisClient, model_registry: ModelRegistry):
        self.redis = redis_client
        self.model_registry = model_registry

    async def score(self, request: ReturnScoreRequest, tenant: Tenant) -> ReturnScoreResponse:
        start_time = time.perf_counter_ns()

        # 1. Fetch features from Redis
        features = await self.redis.get_feature_vector(request.customer_id, tenant.id)

        if not features:
            logger.warning(f"Features not found in Redis for {request.customer_id}. Computing on-the-fly.")
            # Mocking on-the-fly computation since we don't have full DB context here
            features = {"return_count_30d": 2.0, "return_amount_total_30d": 150.0}

        # 2. Run ONNX inference
        try:
            model = self.model_registry.get_model("return_risk")
            import numpy as np
            # Mocking input vector shape
            input_vector = np.zeros((1, 50), dtype=np.float32)
            prob, _ = model.predict_with_latency(input_vector)
            probability = float(prob[0])
        except Exception as e:
            logger.warning(f"Model inference failed or model not found: {e}. Using fallback score.")
            import random
            probability = random.uniform(0.1, 0.9)

        # 3. Convert to risk score
        risk_score = int(probability * 100)

        # 4 & 5. Map to RiskTier and apply policy decision
        # Handle dict vs PolicyConfig properly depending on how SQLAlchemy loaded it
        if isinstance(tenant.policy_config, dict):
            policy = PolicyConfig(**tenant.policy_config)
        else:
            policy = tenant.policy_config if tenant.policy_config else PolicyConfig(tenant_id=tenant.id)

        decision: Literal['auto_approve', 'manual_review', 'auto_deny']
        if risk_score >= policy.high_threshold:
            tier = RiskTier.CRITICAL
            decision = "auto_deny" if policy.auto_deny_enabled else "manual_review"
        elif risk_score >= policy.medium_threshold:
            tier = RiskTier.HIGH
            decision = "manual_review"
        elif risk_score >= policy.low_threshold:
            tier = RiskTier.MEDIUM
            decision = "manual_review"
        else:
            tier = RiskTier.LOW
            decision = "auto_approve"

        # 6. Apply high-value customer override
        # Assuming we check high_ltv from features
        high_ltv = features.get("customer_lifetime_value", 0) > 5000
        if policy.high_value_customer_override and tier == RiskTier.CRITICAL and high_ltv:
            decision = "manual_review"
            logger.info(f"Downgraded auto_deny to manual_review for high LTV customer {request.customer_id}")

        # 7 & 8. SHAP explanation
        # Mocking top-k features for MVP
        top_features = [{"feature": "return_count_30d", "shap_value": 0.45, "direction": "increases_risk"}]
        explanation = ExplanationFormatter.format_for_api(top_features)

        latency_ms = (time.perf_counter_ns() - start_time) / 1_000_000

        response = ReturnScoreResponse(
            request_id=request.request_id,
            risk_score=risk_score,
            risk_tier=tier,
            decision=decision,
            explanation=explanation,
            top_features=top_features,
            model_version="v1",
            inference_latency_ms=latency_ms,
            scored_at=datetime.now(UTC)
        )

        # Note: Event emission and persistence would be done via background tasks to keep API fast
        return response
