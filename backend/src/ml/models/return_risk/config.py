"""Configuration for the Return Risk model."""

FEATURE_NAMES = [
    # Velocity (8)
    "return_count_7d",
    "return_count_30d",
    "return_count_90d",
    "return_rate_30d",
    "return_rate_90d",
    "avg_days_to_return",
    "returns_last_hour",
    "returns_today",
    # Value (8)
    "return_amount_total_30d",
    "return_amount_total_90d",
    "avg_return_amount",
    "return_to_order_amount_ratio",
    "max_single_return_amount",
    "refund_rate_by_value",
    "current_return_amount",
    "current_order_amount",
    # Category (6)
    "category_concentration_score",
    "high_risk_category_flag",
    "category_return_rate",
    "unique_categories_returned",
    "same_category_streak",
    "category_match_purchase_history",
    # Account (6)
    "account_age_days",
    "is_new_account",
    "total_orders",
    "total_spend",
    "avg_order_value",
    "customer_lifetime_value",
    # Device/Behavioral (8)
    "device_fingerprint_count",
    "ip_address_count",
    "shipping_address_count",
    "device_age_days",
    "is_new_device",
    "return_reason_diversity",
    "time_since_delivery_hours",
    "is_weekend_return",
    # Interaction (6)
    "return_amount_to_ltv_ratio",
    "velocity_acceleration_7d_vs_30d",
    "amount_deviation_from_mean",
    "category_x_velocity",
    "new_account_x_high_value",
    "device_count_x_return_rate",
    # Historical Outcome (8)
    "previous_chargebacks",
    "previous_fraud_flags",
    "manual_review_count",
    "denial_rate",
    "override_rate",
    "avg_review_time",
    "escalation_count",
    "last_flag_days_ago",
]

CATEGORICAL_FEATURES = [
    "high_risk_category_flag",
    "is_new_account",
    "is_new_device",
    "is_weekend_return",
]

HYPERPARAMETERS = {
    "objective": "binary",
    "metric": "binary_logloss",
    "num_leaves": 63,
    "learning_rate": 0.05,
    "n_estimators": 500,
    "scale_pos_weight": 19.0,
    "min_child_samples": 20,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "max_depth": -1,
    "verbose": -1,
    "seed": 42,
}

CLASSIFICATION_THRESHOLD = 0.35
