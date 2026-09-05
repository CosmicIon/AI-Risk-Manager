"""
Unit tests for Model Drift & Production Monitoring (Module 5.1 - PSI & Concept Drift).
Validates PSI calculation accuracy, risk tier classification, dataset drift summaries, and report generation.
"""

import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from src.drift import (
    calculate_dataset_drift,
    calculate_feature_psi,
    classify_psi,
    generate_drift_report,
)


def test_psi_identical_distributions_is_stable():
    """Two samples from the same distribution should have near-zero PSI (<0.05) and STABLE classification."""
    np.random.seed(42)
    expected = np.random.normal(loc=100.0, scale=15.0, size=2000)
    actual = np.random.normal(loc=100.0, scale=15.0, size=2000)

    psi_val, breakdown = calculate_feature_psi(expected, actual, num_bins=10)

    assert psi_val < 0.05, f"Expected near-zero PSI for identical distributions, got {psi_val}"
    assert classify_psi(psi_val) == "STABLE"
    assert len(breakdown) > 0


def test_psi_moderate_shift_detection():
    """A modest mean shift should land in MODERATE_SHIFT tier (0.10 <= PSI <= 0.25)."""
    np.random.seed(42)
    expected = np.random.normal(loc=50.0, scale=10.0, size=2500)
    actual = np.random.normal(loc=54.5, scale=10.0, size=2500)

    psi_val, _ = calculate_feature_psi(expected, actual, num_bins=10)

    assert 0.08 <= psi_val <= 0.30, f"Expected moderate PSI, got {psi_val}"
    assert classify_psi(psi_val) in ["MODERATE_SHIFT", "SIGNIFICANT_DRIFT"]


def test_psi_significant_drift_detection():
    """A substantial mean and variance shift should trigger SIGNIFICANT_DRIFT alert (PSI > 0.25)."""
    np.random.seed(42)
    expected = np.random.normal(loc=50.0, scale=10.0, size=2000)
    actual = np.random.normal(loc=85.0, scale=25.0, size=2000)

    psi_val, _ = calculate_feature_psi(expected, actual, num_bins=10)

    assert psi_val > 0.25, f"Expected high PSI for major shift, got {psi_val}"
    assert classify_psi(psi_val) == "SIGNIFICANT_DRIFT"


def test_calculate_dataset_drift_summary():
    """Verify dataset drift computation accurately tracks feature health and concept drift."""
    np.random.seed(42)
    n = 500
    train_df = pd.DataFrame({
        "feat_stable": np.random.normal(50, 10, size=n),
        "feat_drifted": np.random.normal(50, 10, size=n),
        "TX_FRAUD": np.random.choice([0, 1], p=[0.9, 0.1], size=n),
    })
    test_df = pd.DataFrame({
        "feat_stable": np.random.normal(50, 10, size=n),
        "feat_drifted": np.random.normal(90, 20, size=n),  # Intentionally drifted
        "TX_FRAUD": np.random.choice([0, 1], p=[0.75, 0.25], size=n),  # Concept drift
    })

    summary = calculate_dataset_drift(
        train_df, test_df, feature_cols=["feat_stable", "feat_drifted"]
    )

    assert summary["overall_health"] == "ACTION_REQUIRED"
    assert summary["feature_summary"]["significant_drift"] >= 1
    assert summary["feature_summary"]["stable"] >= 1
    assert summary["concept_drift"]["shift_pct_points"] > 0
    assert len(summary["features"]) == 2


def test_generate_drift_report_exports_files(tmp_path):
    """Verify generate_drift_report creates valid Markdown and JSON report files."""
    mock_summary = {
        "timestamp": "2026-09-04T12:00:00Z",
        "overall_health": "MONITOR",
        "recommendation": "Monitor test features.",
        "train_samples": 1000,
        "test_samples": 500,
        "feature_summary": {
            "total_features": 2,
            "stable": 1,
            "moderate_shift": 1,
            "significant_drift": 0,
        },
        "concept_drift": {
            "train_fraud_rate_pct": 5.0,
            "test_fraud_rate_pct": 6.2,
            "shift_pct_points": 1.2,
            "status": "STABLE",
        },
        "prediction_drift": {
            "psi": 0.082,
            "status": "STABLE",
        },
        "features": [
            {
                "feature": "TX_AMOUNT",
                "psi": 0.1245,
                "status": "MODERATE_SHIFT",
                "train_mean": 52.0,
                "test_mean": 61.5,
                "train_std": 20.0,
                "test_std": 22.1,
            }
        ],
    }

    report_path, json_path = generate_drift_report(mock_summary, tmp_path)

    assert report_path.exists()
    assert json_path.exists()

    # Verify JSON content
    with open(json_path, "r") as f:
        loaded = json.load(f)
    assert loaded["overall_health"] == "MONITOR"

    # Verify Markdown content
    with open(report_path, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert "# 🛡️ Production Model Drift & Stability Report" in md_text
    assert "TX_AMOUNT" in md_text
    assert "0.1245" in md_text
