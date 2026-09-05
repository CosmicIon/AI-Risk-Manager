import json
from pathlib import Path
import sys

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import pytest

# Ensure project root is in sys.path
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from src.utils import get_project_root


@pytest.fixture(scope="session", autouse=True)
def ensure_test_assets_exist():
    """
    Session-level autouse fixture.
    Guarantees that models/feature_columns.json and models/model.pkl exist before any test runs.
    This ensures that fresh checkouts in CI environments (like GitHub Actions) pass all tests.
    """
    root = get_project_root()
    models_dir = root / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    feats_path = models_dir / "feature_columns.json"
    canonical_features = [
        "TX_AMOUNT",
        "TX_DURING_WEEKEND",
        "TX_DURING_NIGHT",
        "TX_DIST_CUSTOMER_TERMINAL",
        "CUSTOMER_ID_NB_TX_15MIN_WINDOW",
        "CUSTOMER_ID_NB_TX_1HOUR_WINDOW",
        "TIME_SINCE_LAST_TX",
        "CUSTOMER_ID_NB_TX_1DAY_WINDOW",
        "CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW",
        "CUSTOMER_ID_NB_TX_7DAY_WINDOW",
        "CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW",
        "CUSTOMER_ID_NB_TX_30DAY_WINDOW",
        "CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW",
        "CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW",
        "TX_AMOUNT_ZSCORE",
        "TERMINAL_ID_NB_TX_1DAY_WINDOW",
        "TERMINAL_ID_RISK_1DAY_WINDOW",
        "TERMINAL_ID_NB_TX_7DAY_WINDOW",
        "TERMINAL_ID_RISK_7DAY_WINDOW",
        "TERMINAL_ID_NB_TX_30DAY_WINDOW",
        "TERMINAL_ID_RISK_30DAY_WINDOW",
    ]

    if not feats_path.exists():
        with open(feats_path, "w") as f:
            json.dump(canonical_features, f, indent=4)

    model_path = models_dir / "model.pkl"
    if not model_path.exists():
        # Train a fast, calibrated dummy model for testing
        np.random.seed(42)
        X_dummy = pd.DataFrame(
            np.random.randn(100, len(canonical_features)), columns=canonical_features
        )
        X_dummy["TX_AMOUNT"] = np.random.uniform(10, 500, size=100)
        X_dummy["TX_AMOUNT_ZSCORE"] = (X_dummy["TX_AMOUNT"] - 50.0) / 20.0
        y_dummy = ((X_dummy["TX_AMOUNT"] > 100.0) | (X_dummy["TX_AMOUNT_ZSCORE"] > 2.0)).astype(int)

        dummy_model = lgb.LGBMClassifier(n_estimators=10, random_state=42, verbose=-1)
        dummy_model.fit(X_dummy, y_dummy)
        joblib.dump(dummy_model, model_path)
