FEATURE_NAMES = [
    "evidence_completeness_score",
    "reason_code_historical_win_rate",
    "amount_bucket",
    "days_to_deadline",
    "has_delivery_proof",
    "has_3ds_log",
    "has_avs_match",
    "has_customer_communication",
    "similar_case_best_outcome",
    "merchant_historical_win_rate",
    "network_factor",
    "evidence_item_count",
    "narrative_length",
    "transaction_age_days",
    "customer_dispute_rate",
    "order_velocity_24h",
    "digital_goods_flag",
    "address_mismatch_flag",
    "ip_distance_miles",
    "time_to_dispute_days"
]

def compute_features(chargeback: dict, evidence: dict) -> dict[str, float]:
    """Computes 20 features for chargeback win probability scoring."""
    features = {f: 0.0 for f in FEATURE_NAMES}
    
    # Evidence features
    items = evidence.get("items", [])
    features["evidence_item_count"] = len(items)
    features["evidence_completeness_score"] = evidence.get("completeness_score", 0.0)
    
    for item in items:
        t = item.get("evidence_type")
        if t == "delivery_proof":
            features["has_delivery_proof"] = 1.0
        elif t == "3ds_log":
            features["has_3ds_log"] = 1.0
        elif t == "avs_match":
            features["has_avs_match"] = 1.0
        elif t == "customer_communication":
            features["has_customer_communication"] = 1.0
            
    # Chargeback data
    features["days_to_deadline"] = 15.0 # mock
    features["transaction_age_days"] = 30.0 # mock
    features["time_to_dispute_days"] = 10.0 # mock
    
    return features
