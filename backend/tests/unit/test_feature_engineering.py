from src.ml.models.return_risk.config import FEATURE_NAMES
from src.ml.models.return_risk.features import compute_features


def test_compute_features():
    order = {"order_amount": 100.0, "return_amount": 50.0, "category": "electronics"}
    history = [{"return_amount": 20.0}, {"return_amount": 30.0}]

    features = compute_features("cust_1", order, history)

    assert len(features) == 50
    assert all(f in features for f in FEATURE_NAMES)

    assert features["return_count_30d"] == 2
    assert features["return_amount_total_30d"] == 50.0
    assert features["avg_return_amount"] == 25.0
    assert features["high_risk_category_flag"] == 1.0
    assert features["current_return_amount"] == 50.0
    assert features["current_order_amount"] == 100.0
    assert features["return_to_order_amount_ratio"] == 0.5
