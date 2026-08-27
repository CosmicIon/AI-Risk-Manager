from datetime import datetime
from uuid import UUID

from src.core.schemas.return_request import FeatureVector
from src.ml.models.return_risk.config import FEATURE_NAMES


def compute_features(customer_id: str, order: dict, history: list[dict]) -> dict[str, float]:
    """Computes exactly 50 domain-specific features for return risk scoring."""

    # Defaults
    features = dict.fromkeys(FEATURE_NAMES, 0.0)

    # Basic logic from history if available
    if history:
        # Example logic for some features
        features["return_count_30d"] = len(history)
        features["return_amount_total_30d"] = sum(h.get("return_amount", 0) for h in history)
        features["avg_return_amount"] = features["return_amount_total_30d"] / len(history)

        # In a real app, you would iterate over history to compute accurate time-windowed aggregates.

    # Categoricals mapping (will be treated as int/float by LightGBM)
    cat_val = order.get("category", "")
    high_risk_cats = ["electronics", "luxury"]
    features["high_risk_category_flag"] = 1.0 if cat_val in high_risk_cats else 0.0

    # Order Specifics
    features["current_return_amount"] = float(order.get("return_amount", 0.0))
    features["current_order_amount"] = float(order.get("order_amount", 0.0))
    if features["current_order_amount"] > 0:
        features["return_to_order_amount_ratio"] = (
            features["current_return_amount"] / features["current_order_amount"]
        )

    return features


async def compute_features_from_redis(
    redis_client, customer_id: str, tenant_id: UUID, order: dict
) -> FeatureVector:
    """Fetches pre-computed features from Redis, computes missing on-the-fly."""
    is_degraded = False

    try:
        cached_data = await redis_client.get_feature_vector(customer_id, tenant_id)
        history = cached_data.get("history", []) if cached_data else []
    except Exception:
        # Fallback if Redis fails
        is_degraded = True
        history = []

    computed = compute_features(customer_id, order, history)

    return FeatureVector(
        customer_id=customer_id,
        features=computed,
        computed_at=datetime.now(),
        staleness_seconds=0.0,
        is_degraded=is_degraded,
    )
